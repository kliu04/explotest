"""
Used only for slicing!
Sets up tracer that will track every executed line
"""

import ast
import atexit
import importlib
import os
import sys
import types
from pathlib import Path

from explotest.ast_importer import Finder, tracked_files
from explotest.ast_pruner import ASTPruner
from explotest.ast_rewriter import ASTRewriterB


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
    try:
        # ignore files we don't have access to
        if is_lib_file(filename):
            # print(f"[skip] {filename}")
            return tracer

        path = Path(filename)
        path.resolve()

        # grab the tracker for the current file
        t = tracked_files.get(path)
        if t is None:
            # print(f"[no tracker] {path}")
            return tracer

        lineno = frame.f_lineno
        if event == "line":
            # add lineno as executed
            t.executed_line_numbers.add(lineno)

        return tracer
    except Exception as ex:
        print(f"[error] {filename}:{event}: {ex}")
        print(frame.f_lineno, arg)
        return None


def load_code(root_path: Path, module_name: str):
    """Load user code, patch function calls."""
    finder = Finder(root_path)
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
    sys.settrace(tracer)
    atexit.register(lambda: sys.settrace(None))
    # the next line will run the code!
    load_code(Path(script_dir), Path(target).stem)
    # runpy.run_path(os.path.abspath(target), run_name="__main__")
    sys.settrace(None)

    # after running is complete
    for tf in tracked_files.values():
        pruner = ASTPruner()
        # nodes is the AST repr of the file
        nodes = tf.nodes
        # walk the AST; add attributes to nodes whose lines have been executed
        for node in ast.walk(nodes):
            if hasattr(node, "lineno"):
                if node.lineno in tf.executed_line_numbers:
                    node.executed = True
                else:
                    node.executed = False

        # prune ifs, etc.
        nodes = pruner.visit(tf.nodes)
        nodes = ast.fix_missing_locations(nodes)
        tf.nodes = nodes

        # more rewriting for simplifying grammars
        rewriter = ASTRewriterB(tf)
        nodes = rewriter.rewrite()
        nodes = ast.fix_missing_locations(nodes)

        # Create new module with flattened statements
        print(ast.unparse(nodes))


if __name__ == "__main__":
    main()
