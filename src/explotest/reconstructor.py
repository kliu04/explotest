import abc
from abc import abstractmethod

from explotest.pytest_fixture import PyTestFixture


class Reconstructor(abc.ABC):

    @abstractmethod
    def asts(self, bindings) -> list[PyTestFixture]: ...
