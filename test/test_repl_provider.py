"""
Tests REPLProvider class in repl_provider.py.
"""
import ast

import pytest

from IPython.terminal.interactiveshell import TerminalInteractiveShell


@pytest.fixture
def ipython_shell() -> TerminalInteractiveShell:
    """
    :return: An interactive shell used to run cells of code to test the REPLProvider with.
    """
    return TerminalInteractiveShell()

def test_get_executed_code_blocks(ipython_shell: TerminalInteractiveShell) -> None:
    pass

def test_get_modules(ipython_shell: TerminalInteractiveShell) -> None:
    pass