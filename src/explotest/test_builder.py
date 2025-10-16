import ast
import inspect
from pathlib import Path
from typing import Optional, Any, Self

from .autoassert.autoassert import AssertionResult
from .meta_test import MetaTest
from .reconstructors.abstract_reconstructor import AbstractReconstructor


def is_inside_package(path: Path) -> bool:
    return (path.parent / "__init__.py").exists()


class TestBuilder:

    def __init__(
        self,
        fut_path: Path,
        fut_name: str,
        bound_args: dict[str, Any],
        fut_signature: Optional[inspect.Signature] = None,
    ):
        self.result = MetaTest()
        self.fut_path = fut_path
        self.fut_name = fut_name
        self.parameters = list(bound_args.keys())
        self.arguments = list(bound_args.values())
        self.fut_signature = fut_signature

        self.result.fut_name = self.fut_name
        self.result.fut_parameters = self.parameters

    def build_imports(self, package_name: Optional[str]) -> Self:
        imports: list[ast.Import | ast.ImportFrom] = [
            ast.Import(names=[ast.alias(name="os")]),
            ast.Import(names=[ast.alias(name="dill")]),
            ast.Import(names=[ast.alias(name="pytest")]),
        ]

        # dynamically handle import depending on if inside as a package or running as script
        if package_name is not None and package_name != "":
            # running as module
            imports.append(
                ast.ImportFrom(
                    module=package_name,
                    names=[ast.alias(name=self.fut_path.stem)],
                    level=0,
                )
            )
        elif is_inside_package(self.fut_path):
            # running as script inside a package
            imports.append(
                ast.ImportFrom(
                    module=".",
                    names=[ast.alias(name=self.fut_path.stem)],
                    level=0,
                )
            )
        else:
            # running as script
            imports.append(ast.Import(names=[ast.alias(name=self.fut_path.stem)]))

        self.result.imports = imports
        return self

    def build_fixtures(self, reconstructor: AbstractReconstructor) -> Self:
        fixtures = []
        for parameter, argument in zip(self.parameters, self.arguments):
            new_fixtures = reconstructor.make_fixture(parameter, argument)
            if new_fixtures is None:
                raise ValueError(
                    f"ExploTest failed to generate fixture for {parameter}."
                )
            fixtures.append(new_fixtures)
        self.result.direct_fixtures = fixtures
        return self

    def build_assertions(self, assertion_result: AssertionResult) -> Self:
        self.result.direct_fixtures.extend(assertion_result.fixtures)
        self.result.asserts = assertion_result.assertions
        return self

    def build_act_phase(self) -> Self:
        filename = self.fut_path.stem
        
        # Determine parameter types by checking the function signature
        var_positional_param = None
        var_keyword_param = None
        keyword_only_params = set()
        
        if self.fut_signature is not None:
            for param_name, param in self.fut_signature.parameters.items():
                if param.kind == inspect.Parameter.VAR_POSITIONAL:
                    var_positional_param = param_name
                elif param.kind == inspect.Parameter.VAR_KEYWORD:
                    var_keyword_param = param_name
                elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                    keyword_only_params.add(param_name)
        
        # Separate parameters into positional args, keyword args, *args, and **kwargs
        positional_args = []
        keyword_args = []
        starargs = None
        kwargs = None
        
        for param in self.parameters:
            if param == var_positional_param:
                # Variadic positional parameter (*args)
                starargs = ast.Starred(
                    value=ast.Name(id=param, ctx=ast.Load()), ctx=ast.Load()
                )
            elif param == var_keyword_param:
                # Variadic keyword parameter (**kwargs)
                kwargs = ast.Name(id=param, ctx=ast.Load())
            elif param in keyword_only_params:
                # Keyword-only parameter (must be passed as keyword argument)
                keyword_args.append(
                    ast.keyword(
                        arg=param,
                        value=ast.Name(id=param, ctx=ast.Load())
                    )
                )
            else:
                # Regular positional or positional-or-keyword parameter
                positional_args.append(ast.Name(id=param, ctx=ast.Load()))
        
        # Build args list with starred if needed
        args_list = positional_args
        if starargs:
            args_list.append(starargs)
        
        # Build keywords list with keyword-only params and **kwargs if needed
        keywords_list = keyword_args
        if kwargs:
            keywords_list.append(ast.keyword(arg=None, value=kwargs))
        
        call_ast = ast.Assign(
            targets=[ast.Name(id="return_value", ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(
                    id=f"{filename}.{self.fut_name}",
                    ctx=ast.Load(),
                ),
                args=args_list,
                keywords=keywords_list,
            ),
        )
        call_ast = ast.fix_missing_locations(call_ast)
        self.result.act_phase = call_ast
        return self

    def build_mocks(
        self, to_mock: dict[str, Any], reconstructor: AbstractReconstructor
    ) -> Self:
        # TODO: think about making reconstructor a parameter or take default ones
        """
        Given a dictionary of variables to mock and mock values, generate mock fixtures.
        """
        d = {k: reconstructor.make_fixture(k, v) for k, v in to_mock.items()}

        defn = ast.FunctionDef(
            name="mock_setup",
            args=ast.arguments(
                args=[
                    ast.arg(arg=f"generate_{fixture.parameter}")
                    for fixture in d.values()
                ]
            ),
            body=(
                ([ast.Global(names=list(d.keys()))] if len(d) > 0 else [])
                + [
                    ast.Assign(
                        targets=[ast.Name(id=name, ctx=ast.Store())],
                        value=ast.Name(
                            id=f"generate_{fixture.parameter}", ctx=ast.Load()
                        ),
                    )
                    for name, fixture in d.items()
                ]
                + [ast.Import(names=[ast.alias(name="os")])]
                + [
                    ast.Assign(
                        targets=[
                            ast.Subscript(
                                value=ast.Attribute(
                                    value=ast.Name(id="os", ctx=ast.Load()),
                                    attr="environ",
                                    ctx=ast.Load(),
                                ),
                                slice=ast.Constant(value="RUNNING_GENERATED_TEST"),
                                ctx=ast.Store(),
                            )
                        ],
                        value=ast.Constant(value="true"),
                    )
                ]
            ),
            decorator_list=[
                ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id="pytest", ctx=ast.Load()),
                        attr="fixture",
                        ctx=ast.Load(),
                    ),
                    keywords=[
                        ast.keyword(arg="autouse", value=ast.Constant(value=True))
                    ],
                )
            ],
        )

        self.result.mock = ast.fix_missing_locations(defn)
        return self

    def get_meta_test(self) -> MetaTest:
        return self.result
