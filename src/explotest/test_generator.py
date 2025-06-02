import ast
from _ast import alias
from pathlib import Path
from typing import Dict, Any

from .argument_reconstruction_reconstructor import (
    ArgumentReconstructionReconstructor,
)
from .generated_test import GeneratedTest
from .helpers import Mode
from .helpers import sanitize_name
from .pickle_reconstructor import PickleReconstructor
from .reconstructor import Reconstructor


class TestGenerator:
    function_name: str
    file_path: Path
    reconstructor: Reconstructor

    # TODO: refactor this to use dependency injection
    def __init__(self, function_name: str, file_path: Path, mode: Mode):
        self.function_name = function_name
        self.file_path = file_path

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
            ast.Import(names=[alias(name="pytest")]),
            ast.Import(names=[alias(name=filename)]),
        ]

        return imports

    def generate(self, bindings: Dict[str, Any], definitions: list[ast.FunctionDef | ast.ClassDef | ast.FunctionDef] = None) -> GeneratedTest:
        """
        Creates a test for the function-under-test specified by the TestGenerator.
        Provide a set of parameter bindings (parameter -> value)
        to create a test that reconstructs those bindings into a test.
        """
        if definitions is None:
            definitions = []

        params = list(bindings.keys())
        filename = self.file_path.stem

        asts = self.reconstructor.asts(bindings)
        return_ast = ast.Assign(
            targets=[ast.Name(id="return_value", ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(id=f"{filename}.{self.function_name}", ctx=ast.Load()),
                args=[ast.Name(id=param, ctx=ast.Load()) for param in params],
            ),
        )
        return_ast = ast.fix_missing_locations(return_ast)
        return GeneratedTest(
            sanitize_name(self.function_name),
            self._imports(filename),
            asts,
            return_ast,
            [],
            definitions,
        )
