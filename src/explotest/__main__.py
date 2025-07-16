"""
Used only for slicing!
Sets up tracer that will track every executed line
"""

import ast
import importlib
import os
import sys
import types
from pathlib import Path

from explotest.ast_importer import Finder, tracked_files
from explotest.ast_pruner import ASTPruner
from explotest.ast_rewriter import ASTRewriter


def is_lib_file(filepath: str) -> bool:
    return any(substring in filepath for substring in ("3.13", ".venv", "<frozen"))


def tracer(frame: types.FrameType, event, arg):
    """
    #     Hooks onto Python default tracer to add instrumentation for ExploTest.
    #     :param frame:
    #     :param event:
    #     :param __arg:
    #     :return: must return this object for tracing to work
    """
    filename = frame.f_code.co_filename
    # filename = frame.f_globals.get("__file__", "<unknown>")
    # ignore files we don't have access to
    if is_lib_file(filename):
        return tracer

    path = Path(filename)
    path.resolve()
    try:
        lineno = frame.f_lineno

        t = tracked_files.get(path)
        if t is None:
            return tracer

        if event == "line":
            t.traced_line_numbers.add(lineno)
    except Exception as e:
        print(f"Exception: {e}")

    return tracer


class Transformer(ast.NodeTransformer):

    def visit_Assign(self, node):
        return [node, ast.Pass()]


def load_code(root_path: Path, module_name: str):
    """Load user code, patch function calls."""
    finder = Finder(root_path)
    try:
        sys.meta_path.insert(0, finder)
        module_name = module_name.replace(".py", "")
        return importlib.import_module(module_name)
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
    sys.settrace(tracer)
    load_code(Path(script_dir), target)
    # runpy.run_path(os.path.abspath(target), run_name="__main__")
    sys.settrace(None)

    for tf in tracked_files.values():
        rewriter = ASTRewriter(tf)
        nodes = rewriter.rewrite()
        nodes = ast.fix_missing_locations(nodes)

        pruner = ASTPruner(tf)
        nodes = pruner.visit(nodes)
        nodes = ast.fix_missing_locations(nodes)

        # Create new module with flattened statements
        print(ast.unparse(nodes))


if __name__ == "__main__":
    main()
