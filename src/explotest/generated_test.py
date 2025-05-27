import ast
from dataclasses import dataclass

from src.explotest.pytest_fixture import PyTestFixture


@dataclass
class GeneratedTest:
    fixtures: list[PyTestFixture]
    act_phase: list[ast.Assign]
    asserts: list[ast.Assert]  # probably gonna be empty...

    @property
    def ast_node(self) -> ast.FunctionDef: ...

    def to_file(self) -> None:
        pass
