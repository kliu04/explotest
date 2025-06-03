import pytest
from IPython.core import magic_arguments
from IPython.terminal.interactiveshell import TerminalInteractiveShell

from src.explotest.generated_test import GeneratedTest
from src.explotest.ipy.wrapper import generate_tests_wrapper

def patched_argstring_pickle():
    class Patched:
        filename = "test_output.py"
        lineno = '8'
        mode = "pickle"

    return lambda x, y: Patched()


def patched_argstring_reconstruct():
    class Patched:
        filename = "test_output.py"
        lineno = '8'
        mode = "reconstruct"

    return lambda x, y: Patched()


@pytest.mark.parametrize('patched', [patched_argstring_pickle(), patched_argstring_reconstruct()])
class TestForWrapper:
    @pytest.fixture
    def program(self) -> list[str]:
        return ["""
from math import sin, pi
import pandas as pd
import numpy as np

        """, """
values = pd.read_csv(r"./A17.csv", names=[r"f"])
        """, """
n = values.iloc[-1].name
        """, """
dx = pi/n
        """, """
x_axis = np.arange(0, np.pi + dx, dx)
        """, """
values['x'] = x_axis
        """, """
def tr_rule(f: pd.Series, x: pd.Series, dx: float, R: int):
    return (
        (2 / pi) * dx * (
            (1/2 * f.iloc[0] * sin(R * x.iloc[0])) +
            sum(f.iloc[1:-1] * (x.iloc[1:-1] * R).map(sin)) +
            (1/2 * f.iloc[-1] * sin(R * x.iloc[-1]))
        )
    ) 
        """, """
tr_rule(values['f'], values['x'], dx, 1)
            """]


    @pytest.fixture
    def run_program(self, program: list[str]) -> TerminalInteractiveShell:
        shell = TerminalInteractiveShell()
        shell.run_line_magic('cd', '../test_data')
        for i, line in enumerate(program):
            shell.run_cell(line, store_history=True)
        return shell

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch, patched):
        monkeypatch.setattr(magic_arguments, 'parse_argstring', patched)

    # @pytest.mark.timeout(3) # 3s max for this test.
    @pytest.mark.skip(reason='infinite loop/way too buggy')
    def test_wrapper_generated_test(self, run_program):
        result: GeneratedTest = generate_tests_wrapper(run_program)()
        assert isinstance(result, GeneratedTest)
        assert result.imports


