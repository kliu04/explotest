import ast
from _ast import FunctionDef
from dataclasses import dataclass

from .pytest_fixture import PyTestFixture


@dataclass
class GeneratedTest:
    function_name: str
    imports: list[ast.Import | ast.ImportFrom]  # needed imports for the test file
    fixtures: list[PyTestFixture]  # argument generators
    act_phase: ast.Assign  # calling the function-under-test
    asserts: list[ast.Assert]
    definitions: list[ast.AST]  # for REPL

    @property
    def to_ast(self) -> ast.Module:
        """
        Returns the entire test as a module.
        """
        return ast.Module(
            body=self.imports
            + self.definitions
            + self.fixture_asts
            + [self.act_function_def_ast]
        )

    @property
    def act_function_def_ast(self) -> ast.FunctionDef:
        """
        Returns the function definition that actually performs the function call on the FUT.
        The "act" phase of the arrangement, act and assert phases of a unit test.
        """
        need_to_request_fixtures_for_these_args = (
            self._find_arguments_passed_into_assign_call()
        )
        requested_fixtures = [
            ast.arg(self._request_fixture(a))
            for a in need_to_request_fixtures_for_these_args
        ]

        generated_defn = ast.FunctionDef(
            name=f"test_{self.function_name}",
            args=ast.arguments(args=requested_fixtures),
            body=(self.decompose_steps() + [self.act_phase] + self.asserts),
        )

        return ast.fix_missing_locations(
            generated_defn
        ) 

    def decompose_steps(self) -> list[ast.Assign]:
        """
        Decomposes the fixtures requested to the argument names.
        """
        result = []
        for arg in self._find_arguments_passed_into_assign_call():
            assign = ast.Assign(
                targets=[ast.Name(id=arg, ctx=ast.Store())],
                value=ast.Name(id=self._request_fixture(arg), ctx=ast.Load()),
            )
            result.append(assign)

        return result

    @staticmethod
    def _request_fixture(name: str):
        """
        Returns a variable name plus generate_ in front of it.
        """
        return f"generate_{name}"

    def _find_arguments_passed_into_assign_call(self) -> list[str]:
        """
        Finds all the arguments passed into our function call. E.g.:

        f(x, y)

        will return [x, y]
        """
        res = []
        call = self.act_phase.value
        if not isinstance(call, ast.Call):
            raise ValueError(
                "The assign value you passed into this test is not an ast.Call, meaning it does not invoke a function."
            )
        for arg in call.args:
            if isinstance(arg, ast.Name):
                res.append(arg.id)
        return res

    @property
    def fixture_asts(self) -> list[FunctionDef]:
        """
        Returns all the fixtures as a list of FunctionDef nodes.
        """
        return [fixture.ast_node for fixture in self.fixtures]
