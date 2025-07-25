"""
Data Structure that represents a File, with associated filename, AST, and line numbers that have been executed

"""

import ast
from dataclasses import dataclass

from explotest.ast_transformer import ASTTransformer


@dataclass
class ASTFile:
    filename: str
    node: ast.AST
    executed_line_numbers: set[int]

    def __init__(self, filename, nodes):
        self.filename = filename
        self.node = nodes
        self.executed_line_numbers = set()

    def transform(self, transformer: ASTTransformer) -> None:
        transformer.transform(self)
        ast.fix_missing_locations(self.node)

    def annotate_execution(self) -> None:
        """
        Annotates AST nodes with execution data.
        """
        for node in ast.walk(self.node):
            if hasattr(node, "lineno"):
                node.executed = node.lineno in self.executed_line_numbers

    def annotate_parent(self) -> None:
        """
        Annotates AST nodes with parent data.
        """
        self.node.parent = None
        for n in ast.walk(self.node):
            for child in ast.iter_child_nodes(n):
                child.parent = n

    def reparse(self) -> None:
        self.node = ast.parse(ast.unparse(self.node))

    @property
    def unparse(self):
        return ast.unparse(self.node)

    def __eq__(self, other):
        if not isinstance(other, ASTFile):
            return False
        elif self is other:
            return True
        return (
            self.filename == other.filename
            and self.node == other.node
            and self.executed_line_numbers == other.executed_line_numbers
        )
