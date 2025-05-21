import pytest
from IPython.terminal.interactiveshell import TerminalInteractiveShell

from src.prototype_ipy_explotest.test_generator import TestGenerator


@pytest.mark.parametrize("program,lineno", [
    ["""
x = 3
    """,
     """
 def foo(x): return x * 2
     """,
     """
 foo(3)
     """], 3
])
class SimpleTests:
    @pytest.fixture
    def run_program(self, program: list[str]) -> TerminalInteractiveShell:
        shell = TerminalInteractiveShell()
        for i, line in enumerate(program):
            shell.run_cell(line, store_history=True)
        return shell

    def test_test_generation(self, run_program: TerminalInteractiveShell, lineno: int) -> None:
        tg = TestGenerator(run_program, lineno)
        resulting_test = tg.generate_test()
        assert 1 == len(resulting_test.act_phase)
        assert 1 == len(resulting_test.)
