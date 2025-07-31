import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from explotest.ast_file import ASTFile
from explotest.ast_transformer import ASTTransformer


class ASTTruncator(ast.NodeTransformer, ASTTransformer):

    def __init__(self, lineno: int):
        self.lineno = lineno

    def generic_visit(self, node: ast.AST):
        if hasattr(node, "lineno"):
            if node.lineno > self.lineno:
                return None
        return super().generic_visit(node)

    def transform(self, ast_file: "ASTFile") -> ast.AST:
        return self.visit(ast_file.node)
