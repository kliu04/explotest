import ast
from abc import abstractmethod, ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from explotest.ast_file import ASTFile


class ASTTransformer(ABC):
    @abstractmethod
    def transform(self, ast_file: "ASTFile") -> ast.AST: ...
