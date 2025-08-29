import ast
import inspect
from pathlib import Path
from typing import Optional

from explotest.helpers import flatten
from explotest.meta_test import MetaTest
from explotest.reconstructors.abstract_reconstructor import AbstractReconstructor


class TestBuilder:

    def __init__(self, fut_name: str, fut_path: Path, bound_args: inspect.BoundArguments, reconstructor: type[AbstractReconstructor]):
        self.fut_name = fut_name
        self.fut_path = fut_path
        self.bound_args = bound_args
        self.reconstructor = reconstructor

    def build_test(self) -> Optional[MetaTest]:
        """
        Creates a unit test for the function-under-test.
        :return: a MetaTest if ExploTest can create a meta unit test, and None if it cannot.
        """

        imports = [
            ast.Import(names=[ast.alias(name="os")]),
            ast.Import(names=[ast.alias(name="dill")]),
            ast.Import(names=[ast.alias(name="pytest")]),
            ast.Import(names=[ast.alias(name=self.fut_path.stem)])
        ]

        parameters =list(self.bound_args.arguments.keys())
        arguments = list(self.bound_args.arguments.values())
        
        self.reconstructor = self.reconstructor(self.fut_path)
        
        fixtures = []
        for parameter, argument in zip(parameters, arguments):
            new_fixtures = self.reconstructor.make_fixture(parameter, argument)
            if new_fixtures is None:
                return None
            fixtures.extend(flatten(new_fixtures))
                
        filename = self.fut_path.stem
        return_ast = ast.Assign(
                targets=[ast.Name(id="return_value", ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(
                        id=(
                           f"{filename}.{self.fut_name}"
                        ),
                        ctx=ast.Load(),
                    ),
                    args=[ast.Name(id=param, ctx=ast.Load()) for param in parameters],
                ),
            )
        return_ast = ast.fix_missing_locations(return_ast)

        return MetaTest(self.fut_name, parameters, imports, fixtures, return_ast, [])

    def create_mocks(self):
        raise NotImplementedError("Oop")
    
    def create_asserts(self):
        raise NotImplementedError("Oop")    
    
    # TODO: handle imports
    


    #
    # @staticmethod
    # def create_mocks(ptf_mapping: dict[str, AbstractFixture]) -> ast.FunctionDef:
    #     """
    #     Creates a function that uses the mock_ptf_names
    #     """
    #     defn = ast.FunctionDef(
    #         name="mock_setup",
    #         args=ast.arguments(
    #             args=[
    #                 ast.arg(arg=f"generate_{fixture.parameter}")
    #                 for fixture in ptf_mapping.values()
    #             ]
    #         ),
    #         body=(
    #             [ast.Global(names=list(ptf_mapping.keys()))]
    #             if len(ptf_mapping) > 0
    #             else []
    #             + [
    #                 ast.Assign(
    #                     targets=[ast.Name(id=name, ctx=ast.Store())],
    #                     value=ast.Name(
    #                         id=f"generate_{fixture.parameter}", ctx=ast.Load()
    #                     ),
    #                 )
    #                 for name, fixture in ptf_mapping.items()
    #             ]
    #             + [ast.Import(names=[ast.alias(name="os")])]
    #             + [
    #                 ast.Assign(
    #                     targets=[
    #                         ast.Subscript(
    #                             value=ast.Attribute(
    #                                 value=ast.Name(id="os", ctx=ast.Load()),
    #                                 attr="environ",
    #                                 ctx=ast.Load(),
    #                             ),
    #                             slice=ast.Constant(value="RUNNING_GENERATED_TEST"),
    #                             ctx=ast.Store(),
    #                         )
    #                     ],
    #                     value=ast.Constant(value="true"),
    #                 )
    #             ]
    #         ),
    #         decorator_list=[
    #             ast.Call(
    #                 func=ast.Attribute(
    #                     value=ast.Name(id="pytest", ctx=ast.Load()),
    #                     attr="fixture",
    #                     ctx=ast.Load(),
    #                 ),
    #                 keywords=[
    #                     ast.keyword(arg="autouse", value=ast.Constant(value=True))
    #                 ],
    #             )
    #         ],
    #     )
    #
    #     return ast.fix_missing_locations(defn)
    #
    # def generate(
    #     self,
    #     bindings: Dict[str, Any],
    #     definitions: list[ast.FunctionDef | ast.ClassDef | ast.AsyncFunctionDef] = None,
    #     injected_imports: list[ast.Import | ast.ImportFrom] = None,
    # ) -> AbstractTest:
    #     """
    #     Creates a test for the function-under-test specified by the TestGenerator.
    #     Provide a set of parameter bindings (parameter -> value)
    #     to create a test that reconstructs those bindings into a test.
    #     """
    #     if definitions is None:
    #         definitions = []
    #
    #     params = list(bindings.keys())
    #     filename = self.file_path.stem if str(self.file_path) != "." else None
    #
    #     fixture = self.reconstructor.asts(bindings)
    #     return_ast = ast.Assign(
    #         targets=[ast.Name(id="return_value", ctx=ast.Store())],
    #         value=ast.Call(
    #             func=ast.Name(
    #                 id=(
    #                     f"{filename}.{self.function_name}"
    #                     if filename is not None
    #                     else self.function_name
    #                 ),
    #                 ctx=ast.Load(),
    #             ),
    #             args=[ast.Name(id=param, ctx=ast.Load()) for param in params],
    #         ),
    #     )
    #     return_ast = ast.fix_missing_locations(return_ast)
    #     return AbstractTest(
    #         sanitize_name(self.function_name),
    #         self._imports(filename, injected_imports),
    #         fixture,
    #         return_ast,
    #         [],
    #         definitions,
    #     )
