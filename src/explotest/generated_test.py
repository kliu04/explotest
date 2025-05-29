import ast
from dataclasses import dataclass

from src.explotest.pytest_fixture import PyTestFixture


@dataclass
class GeneratedTest:
    fut_name: str # name of function-under-test
    imports: list[ast.Import]  # needed imports for the test file
    fixtures: list[PyTestFixture]  # argument generators
    act_phase: ast.Assign  # calling the function-under-test
    asserts: list[ast.Assert]  # probably gonna be empty...
    definitions: list[ast.FunctionDef] # for REPL

    @property
    def ast_node(self) -> ast.Module:
        """
        Returns the entire test as a module.
        """
        return ast.Module(body=[])

    @property
    def act_function_def(self) -> ast.FunctionDef:
        """
        Returns the function definition that actually performs the function call on the FUT.
        The "act" phase of the arrange, act and assert phases of a unit test.
        """
        return ast.FunctionDef(name=f'test_{self.fut_name}')




