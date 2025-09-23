import ast
import os
from abc import ABC
from pathlib import Path
from typing import Any, Optional, cast, Self

from ..meta_fixture import MetaFixture


class AbstractReconstructor(ABC):
    def __init__(self, file_path: Path, backup_reconstructor: type[Self] | None = None):
        self.file_path = file_path  # where to place any files, if needed
        os.makedirs(f"{self.file_path.parent}/pickled", exist_ok=True)
        self.backup_reconstructor = (
            backup_reconstructor(file_path) if backup_reconstructor else None
        )

    def make_fixture(self, parameter: str, argument: Any) -> Optional[MetaFixture]:
        """
        :param parameter: The parameter (as a string) to create the MetaFixture for
        :param argument: Runtime value of the argument
        :return: The MetaFixture needed to recreate the argument, or None if ExploTest fails.
        """
        ...

    @staticmethod
    def _make_primitive_fixture(parameter: str, argument: Any) -> MetaFixture:
        """Helper to reconstruct primitives by simple assignment,
        since behaviour should be the same across all reconstruction modes."""

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

        return MetaFixture([], parameter, [generated_ast], ret)
