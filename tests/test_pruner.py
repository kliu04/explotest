import ast
import atexit
import os
import runpy
import sys
import types
from pathlib import Path

import pytest

from explotest.__main__ import is_lib_file
from explotest.ast_file import ASTFile

DIR = "./data"
pathlist = Path(DIR).glob(f"*pruner_input*.py")
files = dict()


@pytest.fixture
def tracer():
    def _tracer(frame: types.FrameType, event, arg):
        """
        #     Hooks onto Python default _tracer to add instrumentation for ExploTest.
        #     :param frame:
        #     :param event:
        #     :param __arg:
        #     :return: must return this object for tracing to work
        """
        filename = frame.f_code.co_filename
        try:
            # ignore files we don't have access to
            if is_lib_file(filename):
                # print(f"[skip] {filename}")
                return _tracer

            path = Path(filename)
            path.resolve()

            if filename not in files:
                with open(filename, "r") as f:
                    ast_file = ASTFile(filename, ast.parse(f.read()))
                    files[filename] = ast_file
            else:
                ast_file = files[filename]

            lineno = frame.f_lineno
            if event == "line":
                ast_file.executed_line_numbers.add(lineno)

            return _tracer
        except Exception as ex:
            print(f"[error] {filename}:{event}: {ex}")
            return None

    return _tracer


@pytest.mark.parametrize("filename", pathlist)
def test_pruner(filename, monkeypatch, tracer):

    # with open(os.devnull, "w") as fnull, redirect_stdout(fnull):
    sys.settrace(tracer)
    atexit.register(lambda: sys.settrace(None))
    runpy.run_path(os.path.abspath(filename), run_name="__main__")
    sys.settrace(None)

    print(files)
