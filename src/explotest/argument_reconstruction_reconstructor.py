from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from src.explotest.helpers import is_primitive
from src.explotest.pickle_reconstructor import PickleReconstructor
from src.explotest.reconstructor import Reconstructor

X = TypeVar("X")


@dataclass(frozen=True)
class ArgumentReconstructionReconstructor(Reconstructor):

    backup_reconstructor: PickleReconstructor

    def __init__(self, file_path: Path):
        # hacky way to get around frozen-ness
        object.__setattr__(self, "backup_reconstructor", PickleReconstructor(file_path))

    def _ast(self, parameter, argument):
        if is_primitive(argument):
            return Reconstructor._reconstruct_primitive(parameter, argument)
        # elif inspect.isfunction(argument):
        #     return self.backup_reconstructor._ast(parameter, argument)
        else:
            return self.backup_reconstructor._ast(parameter, argument)

    @staticmethod
    def _reconstruct_object_instance(obj: X) -> X:
        for attr, value in obj.__dict__.items():
            pass
        return
