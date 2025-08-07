import ast
import inspect
from abc import ABC


class Oracle(ABC):
    def run(
        self, node: ast.AST, collected_args: list[inspect.BoundArguments]
    ) -> bool: ...
