import ast
from abc import ABC, abstractmethod

from explotest.executed_code_block import ExecutedCodeBlock  # type: ignore


class Provider(ABC):

    @abstractmethod
    def get_executed_code_blocks(self) -> list[ExecutedCodeBlock]: ...

    @abstractmethod
    def get_modules(self) -> list[ast.Module]: ...
