import ast
from dataclasses import dataclass

from src.explotest.reconstructor import Reconstructor


@dataclass
class ArgumentReconstructionReconstructor(Reconstructor):
    @property
    def asts(self) -> list[ast.AST]:
        pass