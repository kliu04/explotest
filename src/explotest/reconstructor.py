import abc
from abc import abstractmethod

from src.explotest.pytest_fixture import PyTestFixture


class Reconstructor(abc.ABC):
    """Transforms bindings of params and arguments into fixtures for each param.."""

    @abstractmethod
    def asts(self, bindings) -> list[PyTestFixture]: ...
