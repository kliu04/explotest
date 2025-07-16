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
            t = ASTFile(path.name, tree)
            tracked_files[path] = t

        if event == "line":
            t.traced_line_numbers.add(lineno)
    except Exception as e:
        print(e)

    return tracer


class Transformer(ast.NodeTransformer):

    def visit_Assign(self, node):
        return [node, ast.Pass()]


from importlib.util import spec_from_file_location
import importlib.abc


class Loader(importlib.abc.Loader):
    """Implement importlib.Loader"""

    def __init__(self, run_as_main):
        self.run_as_main = run_as_main

    def exec_module(self, module):

        with open(module.__file__) as f:
            src = f.read()

        tree = ast.parse(src, module.__file__, "exec")
        trans = Transformer()
        patched_tree = trans.visit(tree)
        ast.fix_missing_locations(patched_tree)

        code = compile(patched_tree, module.__file__, "exec")

        if self.run_as_main:
            module.__dict__["__name__"] = "__main__"
            self.run_as_main = False
        exec(code, module.__dict__)

    def create_module(self, spec):
        return None  # Use default module creation


class Finder(importlib.abc.MetaPathFinder):
    """An importlib finder that will handler files from user code directory."""

    def __init__(self, code_dir):
        self.code_dir = code_dir
        self.run_as_main = True

    def find_spec(self, fullname: str, path: list[str], target=None):
        if path:
            mod_path = Path(path[0])
            if not mod_path.is_relative_to(self.code_dir):
                return None
        relative_path = fullname.replace(".", "/")  # json.decoder -> json/decoder
        # NOTE: We currently don't support packages (directory with __init__.py)
        # We'll consider that once there's a concrete user request
        full_path = self.code_dir / (relative_path + ".py")
        if not full_path.is_file():
            return None

        loader = Loader(self.run_as_main)
        self.run_as_main = False
        spec = spec_from_file_location(fullname, full_path, loader=loader)
        return spec


def load_code(root_path: Path, module_name: str):
    """Load user code, patch function calls."""
    finder = Finder(root_path)
    try:
        sys.meta_path.insert(0, finder)
        module_name = module_name.replace(".py", "")
        # module_name = "sherlock_project"
        module_name = "scratchpad"
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
    load_code(Path(script_dir), target_folder)
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
