import ast
from dataclasses import dataclass
from typing import Self


@dataclass
class PyTestFixture:
    depends: list[Self]  # fixture dependencies
    parameter: str  # parameter that this fixture generates
    body: list[ast.AST]  # body of the fixture
    ret: ast.Return | ast.Yield  # return value of the fixture

    @property
    def ast_node(self) -> ast.FunctionDef:
        """
        Return the AST node for this pytest fixture.
        """
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
                body=self.body + [self.ret],
                decorator_list=[pytest_deco],
            )
        )

    def __hash__(self) -> int:  # make the object usable as a dict key / set element
        return hash(ast.unparse(self.ast_node))
