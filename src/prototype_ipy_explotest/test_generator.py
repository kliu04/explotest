import ast
from abc import ABC

from dataclasses import dataclass

from IPython import InteractiveShell
from typing import Iterable

from src.prototype_ipy_explotest.generated_test import GeneratedTest

@dataclass
class IPythonLineRun:
    session_id: int
    input: ast.Module
    output: str | None # why, ipython?

class IPythonExecutionHistory:
    d: dict[int, IPythonLineRun] # mapping of lineno to IPythonLineRun

    def __init__(self, range_result: Iterable[tuple[int, int, tuple[str, str | None]]]):
        self.d = {}
        for session, lineno, in_out  in range_result:
            input = in_out[0]
            output = in_out[1]
            self.d[lineno] = IPythonLineRun(session, ast.parse(input), output)

    def __getitem__(self, item: int):
        return self.d[item]

    def __iter__(self):
        return iter(self.d)

    def __next__(self):
        return next(self.d)






class TestGenerator(ABC):
    history: IPythonExecutionHistory
    invocation_lineno: int
    target_lines: tuple[int, int]
    def __init__(self, shell: InteractiveShell, invocation_lineno: int, target_lines: tuple[int, int] = (-1, -1)):
        session: Iterable[tuple[int, int, tuple[str, str | None]]] = list(shell.history_manager.get_range(output=True))
        self.history = IPythonExecutionHistory(session)
        self.invocation_lineno = invocation_lineno
        self.target_lines = (0, invocation_lineno) if target_lines == (-1, -1) else target_lines

        """
        Initializes a test generator with the given shell.
        Creates a test for specific function invocation on the line provided.
        :param shell: The shell to read execution history from
        :param invocation_lineno: The line that the user called the function-to-test on.
        :param target_lines: The lines to read to "try" to read from. In pickle mode, probably reading all lines is good.
        """

    def generate_test(self) -> GeneratedTest:
        """
        :return: Creates a test created from the execution history of our IPython code.
        """
        return GeneratedTest()

    def _valid_function_call_on_lineno(self) -> bool:
        potential_call = self.history[self.invocation_lineno].input
        return any(type(v.value) == ast.Call for v in potential_call.body) # does the line contain a call?

    def get_call_on_lineno(self) -> ast.Call:
        """
        :return: The highest level ast.Call object on lineno, if it exists
        :raises: Exception (type TBA) if there is no call on lineno
        """
        line_ast = self.history[self.invocation_lineno].input
        for node in line_ast.body:
            if isinstance(node, ast.stmt):
                pass
            elif isinstance(node, ast.expr):
                pass
            else:
                raise Exception('wtf')





    def find_function_params(self) -> dict[str, type]:
        assert self._valid_function_call_on_lineno()
        call = self.history[self.invocation_lineno].input
        call.body[0].value

