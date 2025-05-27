import abc
import ast
from abc import abstractmethod
from dataclasses import dataclass


@dataclass
class Reconstructor(abc.ABC):
    param: str
    value: object

    @property
    @abstractmethod
    def asts(self) -> list[ast.AST]:
        ...