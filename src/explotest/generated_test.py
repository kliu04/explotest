import ast
from dataclasses import dataclass

from src.explotest.pytest_fixture import PyTestFixture


@dataclass
class GeneratedTest:
    imports: list[ast.Import]
    fixtures: list[PyTestFixture]
    act_phase: ast.Assign
    asserts: list[ast.Assert]  # probably gonna be empty...
    definitions: list[ast.FunctionDef] # for REPL

    @property
    def ast_node(self) -> ast.Module: ...
