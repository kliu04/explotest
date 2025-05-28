import ast
from dataclasses import dataclass
from typing import Self


@dataclass
class PyTestFixture:
    depends: list[Self]  # fixture dependencies
    parameter: str  # parameter that this fixture generates
    body: list[  # body of the fixture
        ast.AST
    ]  # TODO: find a way to guarantee that this fixture always returns.

    @property
    def ast_node(self) -> ast.FunctionDef: ...
