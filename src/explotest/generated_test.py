import ast
from dataclasses import dataclass

from src.explotest.pytest_fixture import PyTestFixture


@dataclass(frozen=True)
class GeneratedTest:
    imports: list[ast.Import]  # needed imports for the test file
    fixtures: list[PyTestFixture]  # argument generators
    act_phase: ast.Assign  # calling the function-under-test
    asserts: list[ast.Assert]  # probably gonna be empty...

    @property
    def ast_node(self) -> ast.Module: ...
