import ast

import pytest
from IPython.terminal.interactiveshell import TerminalInteractiveShell

from src.prototype_ipy_explotest.test_generator import TestGenerator


@pytest.fixture
def program() -> list[str]:
    return [
        """
from math import sin, pi
import pandas as pd
import numpy as np
        """,
        """
values = pd.read_csv(r"./A17.csv", names=[r"f"])
        """,
        """
n = values.iloc[-1].name
        """,
        """
dx = pi/n
        """,
        """
x_axis = np.arange(0, np.pi + dx, dx)
        """,
        """
values['x'] = x_axis
        """,
        """
def tr_rule(f: pd.Series, x: pd.Series, dx: float, R: int):
    return (
        (2 / pi) * dx * (
            (1/2 * f.iloc[0] * sin(R * x.iloc[0])) +
            sum(f.iloc[1:-1] * (x.iloc[1:-1] * R).map(sin)) +
            (1/2 * f.iloc[-1] * sin(R * x.iloc[-1]))
        )
    ) 
        """,
        """
tr_rule(values['f'], values['x'], dx, 1)
        """
    ]


@pytest.fixture
def lineno() -> int:
    return 8


@pytest.fixture
def run_program(program: list[str]) -> TerminalInteractiveShell:
    shell = TerminalInteractiveShell()
    shell.run_line_magic('cd', '../test_data')
    for i, line in enumerate(program):
        shell.run_cell(line, store_history=True)
    return shell


@pytest.fixture
def tg(run_program, lineno) -> TestGenerator:
    return TestGenerator(run_program, lineno)


def test_test_generation(tg: TestGenerator) -> None:
    resulting_test = tg.generate_test()
    assert 1 == len(resulting_test.arrange_phase)
    assert 1 == len(resulting_test.act_phase)
    assert 1 == len(resulting_test.assert_phase)


def test_get_call_on_lineno(tg) -> None:
    call = tg.call_on_lineno
    assert type(call) == ast.Call
    assert type(call.func) == ast.Name
    assert call.func.id == 'tr_rule' and type(call.func.ctx) == ast.Load


def test_find_function_params(tg: TestGenerator) -> None:
    assert ['f', 'x', 'dx', 'R'] == tg.find_function_params()


def test_find_function_args(tg: TestGenerator) -> None:
    expected = [
        ast.Subscript(value=ast.Name(id='values', ctx=ast.Load()), slice=ast.Constant(value='f'), ctx=ast.Load()),
        ast.Subscript(value=ast.Name(id='values', ctx=ast.Load()), slice=ast.Constant(value='x'), ctx=ast.Load()),
        ast.Name(id='dx', ctx=ast.Load()),
        ast.Constant(value=1)
    ]

    assert all([ast.unparse(x) == ast.unparse(y) for x, y in zip(expected, tg.find_function_args())])
