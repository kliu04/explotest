import ast

from .helpers import sanitize_name
from .meta_fixture import MetaFixture


class MetaTest:
    """
    Abstract representation of a PyTest unit test for a function.
    """

    fut_name: str  # function-under-test name
    fut_parameters: list[str]  # all parameters needed for the function-under-test
    imports: list[ast.Import | ast.ImportFrom]  # needed imports for the test file
    direct_fixtures: list[MetaFixture] = (
        []
    )  # argument generators for the function-under-test
    act_phase: ast.Assign  # calling the function-under-test
    asserts: list[ast.Assert] = []  # unit test assertions
    mock: ast.FunctionDef | None = None
    # definitions: list[ast.AST]  # for REPL (Kevin: not sure what this does)

    def make_test(self) -> ast.Module:
        """
        Concretize this abstract test into a PyTest unit test.
        """
        return ast.fix_missing_locations(
            ast.Module(
                body=self.imports
                + ([self.mock] if self.mock else [])
                + [fixture.make_fixture() for fixture in self.direct_fixtures]
                + [self._make_main_function()]
            )
        )

    @staticmethod
    def _prepend_generate(s: str):
        return f"generate_{s}"

    def _fixture_to_param(self) -> list[ast.Assign]:
        """
        Adds assignments to convert fixtures into variables.
        For instance, `f = generate_f`
        :return: A list of ast.Assign representing fixture assignments to variables.
        """
        result = [
            ast.Assign(
                targets=[ast.Name(id=param, ctx=ast.Store())],
                value=ast.Name(id=self._prepend_generate(param), ctx=ast.Load()),
            )
            for param in [
                direct_fixture.parameter for direct_fixture in self.direct_fixtures
            ]
        ]

        return result

    def _make_main_function(self) -> ast.FunctionDef:
        """
        Returns the AST of the "main" test function that calls the FUT and concretizes the assertions.
        The "act" and "assert" phase of the arrangement, act and assert phases of a unit test.
        """

        main_function = ast.FunctionDef(
            name=f"test_{sanitize_name(self.fut_name)}",
            # parameters that the main function takes in (requests fixtures)
            args=ast.arguments(
                args=[
                    ast.arg(self._prepend_generate(param))
                    for param in [
                        direct_fixture.parameter
                        for direct_fixture in self.direct_fixtures
                    ]
                ]
            ),
            # pyright: ignore [reportArgumentType]
            body=self._fixture_to_param() + [self.act_phase] + self.asserts,
        )

        return main_function
