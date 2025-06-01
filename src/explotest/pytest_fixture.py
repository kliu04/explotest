import ast
from dataclasses import dataclass
from typing import Self


@dataclass
class PyTestFixture:
    depends: list[Self]  # fixture dependencies
    parameter: str  # parameter that this fixture generates
    body: list[ast.AST]  # body of the fixture
    ret: ast.Return | ast.Yield  # return value of the fixture

    @property
    def ast_node(self) -> ast.FunctionDef: ...
