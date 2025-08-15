import abc
import ast
from abc import abstractmethod
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import cast, Dict, Any, Self

from .pytest_fixture import PyTestFixture


@dataclass
class Reconstructor(abc.ABC):
    """Transforms bindings of params and arguments back into code."""

    file_path: Path
    backup_reconstructor: type[Self] | None = None

    def asts(self, bindings: Dict[str, Any]) -> list[PyTestFixture]:
        """:returns a list of PyTestFixture, which represents each parameter : argument pair"""

        fixtures = {}
        for parameter, argument in bindings.items():
            vertex = self._ast(parameter, argument)
            nodes = self.fixture_bfs(vertex)
            fixtures.update(nodes)

        return list(fixtures)

    @staticmethod
    def fixture_bfs(ptf: PyTestFixture) -> dict[PyTestFixture, None]:
        # bfs on ptf and return all explored edges including itself.
        explored: dict[PyTestFixture, None] = {}
        q: deque[PyTestFixture] = deque()
        q.append(ptf)
        while len(q) != 0:
            current_vertex = q.popleft()
            explored[current_vertex] = None
            for vertex in current_vertex.depends:
                if vertex not in explored:
                    explored[vertex] = None
                    q.append(vertex)
        return explored

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
