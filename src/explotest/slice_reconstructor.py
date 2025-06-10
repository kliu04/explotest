from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .argument_reconstruction_reconstructor import ArgumentReconstructionReconstructor
from .pytest_fixture import PyTestFixture
from .reconstructor import Reconstructor


@dataclass(frozen=True)
class SliceReconstructor(Reconstructor):

    backup_reconstructor: ArgumentReconstructionReconstructor

    def __init__(self, file_path: Path):
        # hacky way to get around frozen-ness
        object.__setattr__(
            self, "backup_reconstructor", ArgumentReconstructionReconstructor(file_path)
        )

    def _ast(self, parameter: str, argument: Any) -> PyTestFixture:
        raise NotImplementedError()
