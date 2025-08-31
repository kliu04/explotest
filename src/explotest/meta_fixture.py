import ast
from dataclasses import dataclass
from typing import Self

from explotest import helpers


@dataclass(frozen=True)
class MetaFixture:
    """
    Abstract representation of a PyTest Fixture that generates a single variable.
    """
    depends: list[Self]  # fixture dependencies (direct only)
    parameter: str  # parameter that this fixture generates
    body: list[ast.stmt]  # body of the fixture
    ret: ast.Return | ast.Yield  # return value of the fixture
    
    def make_fixture(self) -> list[ast.FunctionDef]:
        return self._make_fixture(set())
    
    def _make_fixture(self, seen) -> list[ast.FunctionDef]:
        """
        Concretize this abstract fixture into a PyTest Fixture.

        :return: This MetaFixture as an AST and its dependencies.
        """

        # adds the @pytest.fixture decorator
        pytest_deco = ast.Attribute(
            value=ast.Name(id="pytest", ctx=ast.Load()), attr="fixture", ctx=ast.Load()
        )
        
        if self.parameter in seen:
            return []
        seen.add(self.parameter)
        
        dependency_fixtures = [dep._make_fixture(seen) for dep in self.depends]

        # creates a new function definition with name generate_{parameter}
        return [ast.fix_missing_locations(
            ast.FunctionDef(
                name=f"generate_{self.parameter}",
                args=ast.arguments(
                    args=[
                        ast.arg(arg=f"generate_{dependency.parameter}")
                        for dependency in self.depends
                    ]
                ),
                body= self.body + [self.ret],
                decorator_list=[pytest_deco],
            )
        )] + helpers.flatten(dependency_fixtures)
