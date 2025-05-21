from abc import ABC

from IPython import InteractiveShell

from src.prototype_ipy_explotest.generated_test import GeneratedTest


class TestGenerator(ABC):
    shell: InteractiveShell
    invocation_lineno: int
    target_lines: tuple[int, int]
    def __init__(self, shell: InteractiveShell, invocation_lineno: int, target_lines: tuple[int, int] = (-1, -1)):
        self.shell = shell
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
