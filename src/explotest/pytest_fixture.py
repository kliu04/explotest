import ast
from dataclasses import dataclass
from typing import Self, Optional


@dataclass
class PyTestFixture:
    depends: list[Self]  # fixture dependencies
    parameter: str  # parameter that this fixture generates
    body: list[ast.AST]  # body of the fixture
    # the fixture of the function-under-test does not have a return
    ret: Optional[ast.Return | ast.Yield] = None

    @property
    def ast_node(self) -> ast.FunctionDef: ...
