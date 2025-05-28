import ast
from dataclasses import dataclass
from typing import Self


@dataclass
class PyTestFixture:
    depends: list[Self]  # fixture dependencies
    parameter: str  # parameter that this fixture generates
    body: list[  # body of the fixture
        ast.AST
    ]  # TODO: find a way to guarantee that this fixture always returns.

    @property
    def ast_node(self) -> ast.FunctionDef:
        """
        Return the AST node for this pytest fixture.
        """
        pytest_deco = ast.Attribute(value=ast.Name(id='pytest', ctx=ast.Load()), attr='fixture', ctx=ast.Load())

        # creates a new function definition with name generate_{parameter} and requests the dependent fixtures.
        return ast.fix_missing_locations(ast.FunctionDef(name=f'generate_{self.parameter}', args=ast.arguments(
            args=[ast.arg(arg=f'generate_{dependency.parameter}') for dependency in self.depends]), body=self.body,
                                                         decorator_list=[pytest_deco]))
