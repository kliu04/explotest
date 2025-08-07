from dataclasses import dataclass
from typing import Any

from .pytest_fixture import PyTestFixture
from .reconstructor import Reconstructor


@dataclass
class SliceReconstructor(Reconstructor):

    def _ast(self, parameter: str, argument: Any) -> PyTestFixture:
        raise NotImplementedError()
