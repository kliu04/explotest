from typing import Any

from .pytest_fixture import PyTestFixture
from .reconstructor import Reconstructor


class NullReconstructor(Reconstructor):
    """Returns parameter = None for error cases"""

    def _ast(self, parameter: str, argument: Any) -> PyTestFixture:
        pass
