import ast
from dataclasses import dataclass

from src.explotest.reconstructor import Reconstructor


@dataclass
class PickleReconstructor(Reconstructor):
    @property
    def asts(self) -> list[ast.AST]:
        pass