import ast
import typing
from ast import unparse

import dill
import pytest
from IPython.terminal.interactiveshell import TerminalInteractiveShell

from src.prototype_ipy_explotest.test_generator import TestGenerator


@pytest.fixture
def program() -> list[str]:
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
    expected_imports = {unparse(ast.Import(names=[ast.alias(name='pandas', asname='pd')])),
                        unparse(ast.Import(names=[ast.alias(name='numpy', asname='np')])),
                        unparse(ast.ImportFrom(module='math', names=[ast.alias(name='sin'), ast.alias(name='pi')])),
                        unparse(ast.Import(names=[ast.alias(name='dill')])),
                        unparse(ast.Import(names=[ast.alias(name='pytest')]))}

    assert expected_imports == {unparse(o) for o in resulting_test.imports}

    assert 4 == len(resulting_test.arrange_phase)
    assert 1 == len(resulting_test.act_phase)  # assert 1 == len(resulting_test.assert_phase)


def test_get_call_on_lineno(tg) -> None:
    call = tg.call_on_lineno
    assert isinstance(call, ast.Call)
    assert isinstance(call.func, ast.Name)
    assert call.func.id == 'tr_rule' and type(call.func.ctx) == ast.Load


def test_find_function_params(tg: TestGenerator) -> None:
    assert ['f', 'x', 'dx', 'R'] == tg.find_function_params()


def test_find_function_args(tg: TestGenerator) -> None:
    expected = [
        ast.Subscript(value=ast.Name(id='values', ctx=ast.Load()), slice=ast.Constant(value='f'), ctx=ast.Load()),
        ast.Subscript(value=ast.Name(id='values', ctx=ast.Load()), slice=ast.Constant(value='x'), ctx=ast.Load()),
        ast.Name(id='dx', ctx=ast.Load()), ast.Constant(value=1)]

    assert all([ast.unparse(x) == ast.unparse(y) for x, y in zip(expected, tg.find_function_args())])


def test_pickle_args(tg: TestGenerator) -> None:
    with open('../test_data/f.pkl', 'rb') as f_file, open('../test_data/x.pkl', 'rb') as x_file, open(
            '../test_data/dx.pkl', 'rb') as dx_file, open('../test_data/R.pkl', 'rb') as R_file:
        expected = {'f': dill.load(f_file), 'x': dill.load(x_file), 'dx': dill.load(dx_file), 'R': dill.load(R_file)}

    # unpickle result and check if they're equal
    result = tg.get_args_as_pickles()
    result_transformed: dict[str, typing.Any] = {}

    for k, v in result.items():
        result_transformed[k] = dill.loads(v)

    # noinspection PyTypeChecker
    assert all(expected['f'] == result_transformed['f'])
    # noinspection PyTypeChecker
    assert all(expected['x'] == result_transformed['x'])
    assert expected['dx'] == result_transformed['dx']
    assert expected['R'] == result_transformed['R']


@pytest.mark.parametrize('aut_name', ['f', 'x', 'dx', 'R'])
def test_fixture_generation(tg: TestGenerator, aut_name) -> None:
    f_res = tg.generate_fixture(aut_name)
    assert (len(f_res.stmts) == 1)
    assert (ast.unparse(f_res.stmts[
                            0]) == f"return dill.loads({tg.get_args_as_pickles()[aut_name]})")  # TODO: make fixtures load from disk


def test_tg_create_test(tg: TestGenerator):
    from pathlib import Path
    test_read = Path('../test_data/expected_test.py').read_text()
    compiled = ast.parse(test_read)

    result = unparse(tg.generate_test().ast_node)

    assert unparse(compiled) == result


def test_import_analysis(tg: TestGenerator):
    expected = {unparse(ast.Import(names=[ast.alias(name='pandas', asname='pd')])),
                unparse(ast.Import(names=[ast.alias(name='numpy', asname='np')])),
                unparse(ast.ImportFrom(module='math', names=[ast.alias(name='sin'), ast.alias(name='pi')]))}

    assert expected == {unparse(o) for o in tg.imports}



@pytest.mark.skip
def test_filtering_ctor(run_program, lineno):
    tg = TestGenerator(run_program, lineno, (6, 8))
    assert len(tg.history) == 3