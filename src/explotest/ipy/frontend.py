import ast
from abc import ABC
from dataclasses import dataclass
from typing import Iterable

from IPython import InteractiveShell


@dataclass
class IPythonLineRun:
    session_id: int
    input: ast.Module
    output: str | None  # why, ipython?


class IPythonExecutionHistory:
    d: dict[int, IPythonLineRun]  # mapping of lineno to IPythonLineRun

    def __init__(self, range_result: Iterable[tuple[int, int, tuple[str, str | None]]]):
        self.d = {}
        for session, lineno, in_out in range_result:
            input = in_out[0]
            output = in_out[1]
            try:
                parsed_input = ast.parse(input)
                self.d[lineno] = IPythonLineRun(session, parsed_input, output)
            except SyntaxError:
                print(f"Error on line: {lineno} invalid syntax, ignoring.")

    def __getitem__(self, item: int):
        return self.d[item]

    def __iter__(self):
        return iter(self.d)

    def __next__(self):
        return next(self.__iter__())

    def __len__(self):
        return len(self.d)


class FrontEnd(ABC):
    shell: InteractiveShell
    history: IPythonExecutionHistory
    invocation_lineno: int
    target_lines: tuple[int, int]

    def __init__(
        self,
        shell: InteractiveShell,
        invocation_lineno: int,
        target_lines: tuple[int, int] = (-1, -1),
    ):
        self.shell = shell
        # self.target_lines = (
        #     (0, invocation_lineno) if target_lines == (-1, -1) else target_lines
        # )

        # self.invocation_lineno = invocation_lineno
        session: Iterable[tuple[int, int, tuple[str, str | None]]] = list(
            shell.history_manager.get_range(output=True)
        )

        self.history = IPythonExecutionHistory(session)

        """
        Initializes a test generator with the given shell.
        Creates a test for specific function invocation on the line provided.
        :param shell: The shell to read execution history from
        :param invocation_lineno: The line that the user called the function-to-test on.
        :param target_lines: The lines to read to "try" to read from. In pickle mode, probably reading all lines is good.
        """

    #
    # @property
    # def _ast_node_at_invocation_lineno(self) -> ast.Module:
    #     return self.history[self.invocation_lineno].input
    #
    # # def _valid_function_call_on_lineno(self) -> bool:
    # #     potential_call = self._ast_node_at_invocation_lineno
    # #     assert self.history[self.invocation_lineno].output is not None
    # #     assert isinstance(potential_call, ast.expr)  # should be expr
    # #     return any(type(v.value) == ast.Call for v in potential_call.body)  # does the line contain a call?
    #
    # @property
    # def call_on_lineno(self) -> ast.Call:
    #     """
    #     :return: The highest level ast.Call object on lineno, if it exists
    #     :raises: Exception (type TBA) if there is no call on lineno
    #     """
    #     for node in self._ast_node_at_invocation_lineno.body:
    #         if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
    #             return node.value
    #     raise ValueError(
    #         "No call was found in target line number. Make sure that the line is only a call, not an assignment."
    #     )
    #
    # @property
    # def function_def(self):
    #     """
    #     Returns the function definition of the call on `lineno`, if it is defined.
    #     If you call a external function, it won't be.
    #     """
    #     return self.search_history_for_func_def_with_id(self.call_on_lineno.func.id)

    def search_history_for_func_def_with_id(self, id: str) -> ast.FunctionDef | None:
        def search_helper(node: ast.AST) -> ast.FunctionDef | None:
            for child in ast.walk(node):
                if isinstance(child, ast.FunctionDef) and child.name == id:
                    return child
            return None

        """
        Finds the FunctionDef node in the history where the name is id
        :param id: The function identifier to search for
        :return: Target function nod
        :raises: ValueError if not found
        """
        for line in self.history:
            execution_result = self.history[line].input

            function_def_at_result = search_helper(execution_result)
            if function_def_at_result is not None:
                return function_def_at_result
        return None

    #
    # def find_function_params(self) -> list[str]:
    #     """
    #     Finds the parameters that the function-under-test contains and their types
    #     :return: A dictionary that maps parameter names to their types.
    #     """
    #
    #     result: list[str] = []
    #
    #     call_id = self.call_on_lineno.func.id  # type: ignore
    #     target_func = self.search_history_for_func_def_with_id(call_id)
    #     if target_func is None:
    #         raise ValueError("Function definition not found.")
    #
    #     # TODO: support varargs & kwargs
    #     for arg in (
    #         target_func.args.posonlyargs
    #         + target_func.args.args
    #         + target_func.args.kwonlyargs
    #     ):
    #         result.append(arg.arg)
    #
    #     return result
    #
    # def find_function_args(self) -> list[ast.expr]:
    #     """
    #     Returns the AST nodes of the stuff inside the function all at lineno.
    #     :return:
    #     """
    #     call_node = self.call_on_lineno
    #     return call_node.args
    #
    # def function_params_and_args(self) -> dict[str, object]:
    #     """
    #     Returns the arguments passed into the function, by param : argument-value pairs.
    #     """
    #     # the order of params & args should be the same.
    #     params = self.find_function_params()
    #     args = self.find_function_args()
    #     result: dict[str, str] = {}
    #     for p, a in zip(params, args):
    #         evaluated_arg = self.shell.ev(ast.unparse(a))
    #         result[p] = evaluated_arg
    #     return result
    #
    # @property
    # def repl_imports(self) -> list[ast.Import | ast.ImportFrom]:
    #     """
    #     Returns all the imports used in the REPL run.
    #     """
    #     imports: list[ast.Import | ast.ImportFrom] = []
    #
    #     def search_helper(node: ast.AST) -> Generator[Import | ImportFrom, Any, None]:
    #         for child in ast.walk(node):
    #             if isinstance(child, ast.ImportFrom) or isinstance(child, ast.Import):
    #                 yield child
    #
    #     for line in self.history:
    #         run = self.history[line]
    #         for result in search_helper(run.input):
    #             imports.append(result)
    #
    #     return imports  # stub
