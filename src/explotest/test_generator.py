from typing import Dict

from explotest import Mode
from explotest.argument_reconstruction_reconstructor import (
    ArgumentReconstructionReconstructor,
)
from explotest.pickle_reconstructor import PickleReconstructor
from explotest.reconstructor import Reconstructor
from src.explotest.generated_test import GeneratedTest


class TestGenerator:

    function_name: str
    reconstructor: Reconstructor

    def __init__(self, function_name: str, mode: Mode):
        self.function_name = function_name
        match mode:
            case Mode.RECONSTRUCT:
                self.reconstructor = ArgumentReconstructionReconstructor()
            case Mode.PICKLE:
                self.reconstructor = PickleReconstructor()
            case Mode.SLICE:
                raise NotImplementedError(f"Slicing is currently not supported.")
            case _:
                raise Exception(f"Unknown Mode: {mode}")

    def generate(self, bindings: Dict[str, object]) -> GeneratedTest:
        # TODO: call phase
        return GeneratedTest(self.reconstructor.asts(bindings), [], [])
