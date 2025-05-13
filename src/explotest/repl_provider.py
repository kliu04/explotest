import ast

from .provider import Provider
from .executed_code_block import ExecutedCodeBlock



class REPLProvider(Provider):
    def get_executed_code_blocks(self) -> list[ExecutedCodeBlock]:
        return []

    def get_modules(self) -> list[ast.Module]:
        return []