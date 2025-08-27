import ast
from dataclasses import dataclass
from typing import Self, cast

from typing_extensions import override


@dataclass(frozen=True)
class AbstractFixture:
    """
    Abstract representation of a PyTest Fixture that generates a single variable.
    """
    depends: list[Self]  # fixture dependencies
    parameter: str  # parameter that this fixture generates
    body: list[ast.AST]  # body of the fixture
    ret: ast.Return | ast.Yield  # return value of the fixture

    @property
    def build_fixture(self) -> ast.FunctionDef:
        """
        Concretize this abstract fixture into a PyTest Fixture.
        """

        # adds the @property annotation
        pytest_deco = ast.Attribute(
            value=ast.Name(id="pytest", ctx=ast.Load()), attr="fixture", ctx=ast.Load()
        )

        # creates a new function definition with name generate_{parameter} and requests the dependent fixtures.
        return ast.fix_missing_locations(
            ast.FunctionDef(
                name=f"generate_{self.parameter}",
                args=ast.arguments(
                    args=[
                        ast.arg(arg=f"generate_{dependency.parameter}")
                        for dependency in self.depends
                    ]
                ),
                body=cast(ast.stmt, self.body) + [self.ret],
                decorator_list=[pytest_deco],
            )
        )

    @override
    def __hash__(self) -> int:  # make the object usable as a dict key / set element
        return hash(ast.unparse(self.build_fixture))
