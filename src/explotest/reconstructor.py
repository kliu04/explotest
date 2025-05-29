import abc
import ast
from abc import abstractmethod
from typing import cast

from src.explotest.pytest_fixture import PyTestFixture


class Reconstructor(abc.ABC):
    """Transforms bindings of params and arguments back into code."""

    @abstractmethod
    def asts(self, bindings) -> list[PyTestFixture]: ...

    @staticmethod
    def reconstruct_primitive(parameter, argument) -> PyTestFixture:
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
        return PyTestFixture([], parameter, [generated_ast])
