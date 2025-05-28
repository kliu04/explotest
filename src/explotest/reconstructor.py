import abc
from abc import abstractmethod

from explotest.pytest_fixture import PyTestFixture


class Reconstructor(abc.ABC):
    """Transforms bindings of params and arguments back into code."""

    @abstractmethod
    def asts(self, bindings) -> list[PyTestFixture]: ...
