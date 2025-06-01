import abc
import ast
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import cast, Dict, Any

from src.explotest.pytest_fixture import PyTestFixture


@dataclass(frozen=True)
class Reconstructor(abc.ABC):
    """Transforms bindings of params and arguments back into code."""

    filepath: Path  # path to write pickled files to

    def asts(self, bindings: Dict[str, Any]) -> list[PyTestFixture]:
        """:returns a list of PyTestFixture, which represents each parameter : argument pair"""
        fixtures = []
        for parameter, argument in bindings.items():
            fixtures.append(self._ast(parameter, argument))
        return fixtures

    @abstractmethod
    def _ast(self, parameter: str, argument: Any) -> PyTestFixture: ...

    @staticmethod
    def _reconstruct_primitive(parameter: str, argument: Any) -> PyTestFixture:
        """Helper to reconstruct primitives, since behaviour should be the same across all reconstruction modes."""
        # need to cast here to not confuse mypy
        generated_ast = cast(
            ast.AST,
            # assign each primitive its argument as a constant
            ast.Assign(
                targets=[ast.Name(id=parameter, ctx=ast.Store())],
                value=ast.Constant(value=argument),
            ),
        )
        # add lineno and col_offset attributes
        generated_ast = ast.fix_missing_locations(generated_ast)

        # add
        ret = ast.fix_missing_locations(
            ast.Return(value=ast.Name(id=parameter, ctx=ast.Load()))
        )

        return PyTestFixture([], parameter, [generated_ast], ret)
