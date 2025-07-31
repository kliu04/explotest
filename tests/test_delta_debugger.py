import ast
from pathlib import Path

import dill
import pytest

from explotest.__main__ import ddmin

DIR = "./data"
argslist = Path(DIR).glob(f"*delta_debugger_args_input*.pkl")


@pytest.fixture
def setup_example():
    def _load_ast(name: str):
        with open(f"./data/{name}.py") as f:
            return ast.parse(f.read())

    return _load_ast


@pytest.mark.parametrize("args_input", argslist)
def test_delta_debugger(args_input, setup_example):
    ast_input_file = Path(str(args_input).replace("args", "ast_file"))
    expected_filename = (
        str(args_input.stem).replace("args_input", "expected").replace(".pkl", ".py")
    )
    expected_ast = setup_example(expected_filename)

    with open(ast_input_file, "rb") as f_ast, open(args_input, "rb") as f_args:
        input_ast = dill.loads(f_ast.read())
        args = dill.loads(f_args.read())

    reduced_ast = ddmin(input_ast, args)

    assert ast.dump(expected_ast) == ast.dump(reduced_ast)
