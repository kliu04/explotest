import ast
from dataclasses import dataclass
from typing import Self


@dataclass
class PyTestFixture:
    depends: list[Self]
    parameter: str
    body: list[
        ast.AST
    ]  # TODO: find a way to guarantee that this fixture always returns.

    @property
    def ast_node(self) -> ast.FunctionDef: ...
