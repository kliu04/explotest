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
from .pytest_fixture import PyTestFixture
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
            case Mode.ARR:
                self.reconstructor = ArgumentReconstructionReconstructor(
                    file_path, PickleReconstructor
                )
            case Mode.PICKLE:
                self.reconstructor = PickleReconstructor(file_path)
            # case Mode.SLICE:
            #     self.reconstructor = SliceReconstructor(file_path)
            case _:
                raise Exception(f"Unknown Mode: {mode}")

    def _imports(
        self, filename: str, inject: list[ast.Import | ast.ImportFrom] | None = None
    ) -> list[ast.Import | ast.ImportFrom]:
        """
        Returns all the imports required for this test.
        """
        imports = [
            ast.Import(names=[alias(name="dill")]),
            ast.Import(names=[alias(name="pytest")]),
        ]

        if inject is not None:
            imports += inject
        else:
            imports += [ast.Import(names=[alias(name=filename)])]

        return imports

    @staticmethod
    def create_mocks(ptf_mapping: dict[str, PyTestFixture]) -> ast.FunctionDef:
        """
        Creates a function that uses the mock_ptf_names
        """
        defn = ast.FunctionDef(
            name="mock_setup",
            args=ast.arguments(
                args=[
                    ast.arg(arg=f"generate_{fixture.parameter}")
                    for fixture in ptf_mapping.values()
                ]
            ),
            body=(
                [ast.Global(names=ptf_mapping.keys())]
                if len(ptf_mapping) > 0
                else []
                + [
                    ast.Assign(
                        targets=[ast.Name(id=name, ctx=ast.Store())],
                        value=ast.Name(
                            id=f"generate_{fixture.parameter}", ctx=ast.Load()
                        ),
                    )
                    for name, fixture in ptf_mapping.items()
                ]
                + [ast.Import(names=[ast.alias(name="os")])]
                + [
                    ast.Assign(
                        targets=[
                            ast.Subscript(
                                value=ast.Attribute(
                                    value=ast.Name(id="os", ctx=ast.Load()),
                                    attr="environ",
                                    ctx=ast.Load(),
                                ),
                                slice=ast.Constant(value="RUNNING_GENERATED_TEST"),
                                ctx=ast.Store(),
                            )
                        ],
                        value=ast.Constant(value="true"),
                    )
                ]
            ),
            decorator_list=[
                ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id="pytest", ctx=ast.Load()),
                        attr="fixture",
                        ctx=ast.Load(),
                    ),
                    keywords=[
                        ast.keyword(arg="autouse", value=ast.Constant(value=True))
                    ],
                )
            ],
        )

        return ast.fix_missing_locations(defn)

    def generate(
        self,
        bindings: Dict[str, Any],
        definitions: list[ast.FunctionDef | ast.ClassDef | ast.AsyncFunctionDef] = None,
        injected_imports: list[ast.Import | ast.ImportFrom] = None,
    ) -> GeneratedTest:
        """
        Creates a test for the function-under-test specified by the TestGenerator.
        Provide a set of parameter bindings (parameter -> value)
        to create a test that reconstructs those bindings into a test.
        """
        if definitions is None:
            definitions = []

        params = list(bindings.keys())
        filename = self.file_path.stem if str(self.file_path) != "." else None

        fixture = self.reconstructor.asts(bindings)
        return_ast = ast.Assign(
            targets=[ast.Name(id="return_value", ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(
                    id=(
                        f"{filename}.{self.function_name}"
                        if filename is not None
                        else self.function_name
                    ),
                    ctx=ast.Load(),
                ),
                args=[ast.Name(id=param, ctx=ast.Load()) for param in params],
            ),
        )
        return_ast = ast.fix_missing_locations(return_ast)
        return GeneratedTest(
            sanitize_name(self.function_name),
            self._imports(filename, injected_imports),
            fixture,
            return_ast,
            [],
            definitions,
        )
