import ast
from _ast import alias
from pathlib import Path
from typing import Dict

from src.explotest import Mode
from src.explotest import reconstructor
from src.explotest.argument_reconstruction_reconstructor import (
    ArgumentReconstructionReconstructor,
)
from src.explotest.generated_test import GeneratedTest
from src.explotest.pickle_reconstructor import PickleReconstructor
from src.explotest.reconstructor import Reconstructor


class TestGenerator:

    function_name: str
    file_path: Path
    reconstructor: Reconstructor

    def __init__(self, function_name: str, file_path: Path, mode: Mode):
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
        params = list(bindings.keys())
        filename = self.file_path.stem
        imports = []

        # if in pickle mode, need to import dill to unpickle
        if isinstance(reconstructor, PickleReconstructor):
            imports.append(ast.Import(names=[alias(name="dill")]))

        imports.append(ast.Import(names=[alias(name=filename)]))

        # need to be like ast.Assign (ast.Call ...)

        return GeneratedTest(
            imports,
            self.reconstructor.asts(bindings),
            ast.Assign(
                targets=[ast.Name(id="return_value", ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(
                        id=f"{filename}.{self.function_name}", ctx=ast.Load()
                    ),
                    args=[ast.Name(id=param, ctx=ast.Load()) for param in params],
                ),
            ),
            [],
        )
