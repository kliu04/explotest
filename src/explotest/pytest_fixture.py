import ast
from dataclasses import dataclass
from typing import Self


@dataclass
class PyTestFixture:
    depends: list[Self]
    parameter: str
    body: list[ast.AST]  # TODO: find a way to guarantee that this fixture always returns.

    @property
    def ast_node(self) -> ast.FunctionDef:
        return ast.fix_missing_locations(ast.FunctionDef(name=f'generate_{self.parameter}', args=ast.arguments(
            args=[ast.arg(arg=f'generate_{dependency.parameter}') for dependency in self.depends]), body=self.body,
                                                         decorator_list=[
                                                             ast.Attribute(value=ast.Name(id='pytest', ctx=ast.Load()),
                                                                           attr='fixture', ctx=ast.Load())]))
