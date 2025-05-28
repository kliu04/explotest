from src.explotest.pytest_fixture import PyTestFixture
from src.explotest.reconstructor import Reconstructor


class ArgumentReconstructionReconstructor(Reconstructor):

    def asts(self, bindings) -> list[PyTestFixture]:
        return []
