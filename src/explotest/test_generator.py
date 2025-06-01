import ast
import os
from _ast import alias
from pathlib import Path
from typing import Dict, Any

from src.explotest.argument_reconstruction_reconstructor import (
    ArgumentReconstructionReconstructor,
)
from src.explotest.generated_test import GeneratedTest
from src.explotest.helpers import Mode
from src.explotest.pickle_reconstructor import PickleReconstructor
from src.explotest.reconstructor import Reconstructor


class TestGenerator:
    function_name: str
    file_path: Path
    reconstructor: Reconstructor

    # TODO: refactor this to use dependency injection
    def __init__(self, function_name: str, file_path: Path, mode: Mode):
        self.function_name = function_name
        self.file_path = file_path

        # make and clear pickled directory
        os.makedirs(f"{file_path}/pickled", exist_ok=True)
        for root, _, files in os.walk(f"{file_path}/pickled"):
            for file in files:
                os.remove(os.path.join(root, file))

        match mode:
            case Mode.RECONSTRUCT:
                self.reconstructor = ArgumentReconstructionReconstructor(file_path)
            case Mode.PICKLE:
                self.reconstructor = PickleReconstructor(file_path)
            case Mode.SLICE:
                raise NotImplementedError(f"Slicing is currently not supported.")
            case _:
                raise Exception(f"Unknown Mode: {mode}")

    def _imports(self, filename: str) -> list[ast.Import | ast.ImportFrom]:
        """
        Returns all the imports required for this test.
        """
        imports = [
            ast.Import(names=[alias(name="dill")]),
            ast.Import(names=[alias(name=filename)]),
        ]

        return imports

    def generate(self, bindings: Dict[str, Any]) -> GeneratedTest:
        """
        Creates a test for the function-under-test specified by the TestGenerator.
        Provide a set of parameter bindings (parameter -> value)
        to create a test that reconstructs those bindings into a test.
        """
        params = list(bindings.keys())
        filename = self.file_path.stem

        asts = self.reconstructor.asts(bindings)

        assignment = ast.Assign(
            targets=[ast.Name(id="return_value", ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(id=f"{filename}.{self.function_name}", ctx=ast.Load()),
                args=[ast.Name(id=param, ctx=ast.Load()) for param in params],
            ),
        )

        assignment = ast.fix_missing_locations(assignment)

        return GeneratedTest(
            self._imports(filename),
            asts,
            assignment,
            [],
            [],
        )
