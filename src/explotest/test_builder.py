import ast
from pathlib import Path
from typing import Optional, Any

from .meta_test import MetaTest
from .reconstructors.abstract_reconstructor import AbstractReconstructor


class TestBuilder:

    def __init__(
        self,
        fut_name: str,
        fut_path: Path,
        bound_args: dict[str, Any],
        reconstructor: type[AbstractReconstructor],
        package_name: Optional[str],
    ):
        self.mock = None
        self.fut_name = fut_name
        self.fut_path = fut_path
        self.bound_args = bound_args
        self.reconstructor = reconstructor
        self.reconstructor = self.reconstructor(self.fut_path)
        self.package_name = package_name

    def build_test(self) -> Optional[MetaTest]:
        """
        Creates a unit test for the function-under-test.
        :return: a MetaTest if ExploTest can create a meta unit test, and None if it cannot.
        """

        imports: list[ast.Import | ast.ImportFrom] = [
            ast.Import(names=[ast.alias(name="os")]),
            ast.Import(names=[ast.alias(name="dill")]),
            ast.Import(names=[ast.alias(name="pytest")]),
        ]

        # dynamically handle import depending on if running as a package or script
        if self.package_name is None:
            imports.append(ast.Import(names=[ast.alias(name=self.fut_path.stem)]))
        else:
            imports.append(
                ast.ImportFrom(
                    module=self.package_name, names=[ast.alias(name=self.fut_path.stem)]
                )
            )

        parameters = list(self.bound_args.keys())
        arguments = list(self.bound_args.values())

        fixtures = []
        for parameter, argument in zip(parameters, arguments):
            new_fixtures = self.reconstructor.make_fixture(parameter, argument)
            if new_fixtures is None:
                return None
            fixtures.append(new_fixtures)

        filename = self.fut_path.stem
        return_ast = ast.Assign(
            targets=[ast.Name(id="return_value", ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(
                    id=f"{filename}.{self.fut_name}",
                    ctx=ast.Load(),
                ),
                args=[ast.Name(id=param, ctx=ast.Load()) for param in parameters],
            ),
        )
        return_ast = ast.fix_missing_locations(return_ast)

        return MetaTest(
            self.fut_name, parameters, imports, fixtures, return_ast, [], self.mock
        )

    def build_mocks(self, d: dict[str, Any]):
        d = {k: self.reconstructor.make_fixture(k, v) for k, v in d.items()}
        """
        Given a dictionary of variables to mock and mock values, generate mock fixtures.
        """
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

        self.mock = ast.fix_missing_locations(defn)

    def create_asserts(self):
        raise NotImplementedError("Oop")
