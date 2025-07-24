"""
Runs the ExploTest dynamic tracer and AST rewriter pipeline.

Namely:
- Sets a tracing hook to monitor executed lines during program execution.
- Applies pruning and rewriting passes to simplify the AST using both static and dynamic data.

Usage: python -m explotest <target.py>
"""

import atexit
import importlib
import os
import sys
import types
from pathlib import Path
from typing import Callable

from explotest.ast_file import ASTFile
from explotest.ast_importer import Finder
from explotest.ast_pruner import ASTPruner
from explotest.ast_rewriter import ASTRewriterB


def is_lib_file(filepath: str) -> bool:
    return any(substring in filepath for substring in ("3.13", ".venv", "<frozen"))


class ASTTracker:
    def __init__(self):
        self.files: dict[Path, ASTFile] = {}

    def get(self, path: Path) -> ASTFile | None:
        return self.files.get(path)

    def add(self, path: Path, file: ASTFile):
        self.files[path] = file

    @property
    def all_files(self) -> list[ASTFile]:
        return list(self.files.values())


def make_tracer(ctx: ASTTracker) -> Callable:
    def _tracer(frame: types.FrameType, event, arg):
        """
        Hooks onto default tracer to add instrumentation for ExploTest.
        :param frame: the current python frame
        :param event: the current event (one-of "line", "call", "return")
        :param arg: currently not used
        :return: must return this object for tracing to work
        """
        filename = frame.f_code.co_filename
        try:
            # ignore files we don't have access to
            if is_lib_file(filename):
                # print(f"[skip] {filename}")
                return _tracer

            path = Path(filename)
            path.resolve()

            # grab the tracker for the current file
            ast_file = ctx.get(path)
            if ast_file is None:
                return _tracer

            # mark lineno as executed
            lineno = frame.f_lineno
            if event == "line":
                ast_file.executed_line_numbers.add(lineno)

            return _tracer
        except Exception as ex:
            print(f"[error] {filename}:{event}: {ex}")
            return None

    return _tracer


def load_code(root_path: Path, module_name: str, ctx: ASTTracker):
    """Load user code, patch function calls."""
    finder = Finder(root_path, ctx)
    try:
        # insert our custom finder into the "meta-path", import the module
        sys.meta_path.insert(0, finder)
        return importlib.import_module(module_name)
    except Exception as ex:
        print(f"[error] {module_name}:{ex}")
    finally:
        sys.meta_path.pop(0)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 -m explotest <filename>")
        sys.exit(1)

    target = sys.argv[1]
    target_folder = os.path.dirname(target)
    sys.argv = sys.argv[1:]

    script_dir = os.path.abspath(target_folder)
    sys.path.insert(0, script_dir)

    # TODO: make this work for modules
    ctx = ASTTracker()
    tracer = make_tracer(ctx)
    sys.settrace(tracer)
    atexit.register(lambda: sys.settrace(None))
    # the next line will run the code and rewriterA
    load_code(Path(script_dir), Path(target).stem, ctx)
    # runpy.run_path(os.path.abspath(target), run_name="__main__")
    sys.settrace(None)

    for ast_file in ctx.all_files:
        # prune ast based on execution paths
        ast_file.transform(ASTPruner())

        # unpack compound statements
        ast_file.transform(ASTRewriterB())

        print(ast_file.unparse)


if __name__ == "__main__":
    main()
