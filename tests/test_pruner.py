import ast
import atexit
import os
import runpy
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from explotest.__main__ import make_tracer, ASTTracker
from explotest.ast_file import ASTFile
from explotest.ast_pruner import ASTPruner

DIR = "./data"
pathlist = Path(DIR).glob(f"*pruner_input*.py")
files: dict[str, ASTFile] = {}

@pytest.fixture
def setup_example():
    def _load_ast(name: str):
        with open(f"./data/{name}.py") as f:
            return ast.parse(f.read())

    return _load_ast


@pytest.mark.parametrize("filename", pathlist)
def test_pruner(filename: Path, setup_example):

    files.clear()

    with open(os.devnull, "w") as fnull, redirect_stdout(fnull):
        ctx = ASTTracker()
        tracer = make_tracer(ctx)
        sys.settrace(tracer)
        atexit.register(lambda: sys.settrace(None))
        runpy.run_path(os.path.abspath(filename), run_name="__main__")
        sys.settrace(None)

    for ast_file in ctx.all_files:
        ast_file.annotate_execution()
        ast_file.transform(ASTPruner())

        expected_name = filename.stem.replace("input", "expected")
        assert ast.dump(ast_file.node) == ast.dump(setup_example(expected_name))
