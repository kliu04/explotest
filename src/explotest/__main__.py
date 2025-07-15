"""
Used only for slicing!
Sets up tracer that will track every executed line
"""

import ast
import os
import runpy
import sys
import types
from pathlib import Path

from explotest.ast_file import ASTFile
from explotest.ast_pruner import ASTPruner
from explotest.ast_rewriter import ASTRewriter

tracked_files: dict[Path, ASTFile] = {}


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
        source = path.read_text()
        lineno = frame.f_lineno

        if tracked_files.get(path):
            t = tracked_files[path]
        else:
            tree = ast.parse(source, filename=path.name)
            t = ASTFile(tree)
            tracked_files[path] = t

        if event == "line":
            t.traced_line_numbers.add(lineno)
    except Exception as e:
        print(e)

    return tracer


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 -m explotest <filename>")
        sys.exit(1)

    target = sys.argv[1]
    sys.argv = sys.argv[1:]

    script_dir = os.path.abspath(os.path.dirname(target))
    sys.path.insert(0, script_dir)

    # TODO: make this work for modules
    sys.settrace(tracer)
    runpy.run_path(os.path.abspath(target), run_name="__main__")
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
