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
        self.node = transformer.transform(self)
        self.node = ast.fix_missing_locations(self.node)

    def annotate_execution(self) -> None:
        """
        Annotates AST nodes with execution data.
        """
        for node in ast.walk(self.node):
            if hasattr(node, "lineno"):
                if node.lineno in self.executed_line_numbers:
                    node.executed = True
                else:
                    node.executed = False

    def annotate_parent(self) -> None:
        """
        Annotates AST nodes with parent data.
        :param node: AST node to annotate
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
