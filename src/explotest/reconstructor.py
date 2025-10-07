import abc
from abc import abstractmethod
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Self

from .meta_fixture import MetaFixture


@dataclass
class Reconstructor(abc.ABC):
    """Transforms bindings of params and arguments back into code."""

    file_path: Path
    backup_reconstructor: type[Self] | None = None

    def asts(self, bindings: Dict[str, Any]) -> list[MetaFixture]:
        """:return: a list of PyTestFixture, which represents each parameter : argument pair"""

        fixtures = {}
        for parameter, argument in bindings.items():
            vertex = self._ast(parameter, argument)
            nodes = self.fixture_bfs(vertex)
            fixtures.update(nodes)

        return list(fixtures)

    @staticmethod
    def fixture_bfs(ptf: MetaFixture) -> dict[MetaFixture, None]:
        # bfs on ptf and return all explored edges including itself.
        explored: dict[MetaFixture, None] = {}
        q: deque[MetaFixture] = deque()
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
    def _ast(self, parameter: str, argument: Any) -> MetaFixture: ...
