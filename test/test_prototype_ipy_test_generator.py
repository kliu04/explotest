import pytest
from IPython.terminal.interactiveshell import TerminalInteractiveShell

from src.prototype_ipy_explotest.test_generator import TestGenerator


@pytest.fixture
def program() -> list[str]:
    return ['x = 3', 'def foo(x): return x * 2', 'foo(x)']

@pytest.fixture
def lineno() -> int:
    return 3

@pytest.fixture
def run_program(program: list[str]) -> TerminalInteractiveShell:
    shell = TerminalInteractiveShell()
    for i, line in enumerate(program):
        shell.run_cell(line, store_history=True)
    return shell

@pytest.fixture
def tg(run_program, lineno) -> TestGenerator:
    return TestGenerator(run_program, lineno)

def test_test_generation(tg) -> None:
    resulting_test = tg.generate_test()
    assert 1 == len(resulting_test.arrange_phase)
    assert 1 == len(resulting_test.act_phase)
    assert 1 == len(resulting_test.assert_phase)

def test_find_function_params(tg):
    assert {'x': int} == tg.find_function_params()