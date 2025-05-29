from explotest.pytest_fixture import PyTestFixture
from src.explotest.reconstructor import Reconstructor


class ArgumentReconstructionReconstructor(Reconstructor):

    def asts(self, bindings) -> list[PyTestFixture]:
        fixtures = []
        for parameter, argument in bindings.items():
            pass
        return []
