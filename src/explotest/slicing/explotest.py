"""
Used only for slicing!
Sets up tracer that will track every executed line
"""

import ast
import os
import runpy
import sys
import sysconfig
import types
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TrackedFile:
    nodes: ast.Module
    executed_lines: set[int] = field(default_factory=set)

tracked_files : dict[Path, TrackedFile] = {}

# TODO: check if OS independent
def is_stdlib_file(filepath: str) -> bool:
    """Determine if a file is part of the standard library;
    E.g., /Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/..."""
    stdlib_path = sysconfig.get_path("stdlib")
    abs_filename = os.path.abspath(filepath)
    abs_stdlib_path = os.path.abspath(stdlib_path)
    return abs_filename.startswith(abs_stdlib_path)


def is_venv_file(filepath: str) -> bool:
    return ".venv" in filepath


def is_frozen_file(filepath: str) -> bool:
    return filepath.startswith("<frozen ")


ast_cache: dict[Path, dict[int, list[ast.AST]]] = (
    {}
)  # open files -> (lineno -> ast) mapping


class TraceAST(ast.NodeTransformer):
    executed_lines: set[int]

    def visit_If(self, node):
        body_linenos = set(getattr(n, "lineno") for n in node.body if hasattr(n, "lineno"))
        if self.executed_lines.intersection(body_linenos):
            return ast.If(
                node.test, list(map(self.generic_visit, node.body)), [ast.Pass()]
            )
        else:
            return ast.If(
                node.test, [ast.Pass()], list(map(self.generic_visit, node.orelse))
            )

    def visit_For(self, node):
        body_linenos = set(getattr(n, "lineno") for n in node.body if hasattr(n, "lineno"))

        # condition is false
        if not self.executed_lines.intersection(body_linenos):
            return ast.For(node.target, node.iter, [ast.Pass()], list(map(self.generic_visit, node.orelse)))
        return super().generic_visit(node)

    def generic_visit(self, node):
        return super().generic_visit(node)


def tracer(frame: types.FrameType, event, arg):
    """
    #     Hooks onto Python default tracer to add instrumentation for ExploTest.
    #     :param frame:
    #     :param event:
    #     :param __arg:
    #     :return: must return this object for tracing to work
    """
    filename = frame.f_globals.get("__file__", "<unknown>")
    # ignore files we don't have access to
    if is_frozen_file(filename) or is_stdlib_file(filename) or is_venv_file(filename):
        return tracer

    path = Path(filename)
    path.resolve()

    source = path.read_text()
    lineno = frame.f_lineno

    if tracked_files.get(path):
        t = tracked_files[path]
    else:
        tree = ast.parse(source, filename=path.name)
        t = TrackedFile(tree)
        tracked_files[path] = t

    if event == "line":
        t.executed_lines.add(lineno)

    return tracer


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 -m explotest <filename>")
        sys.exit(1)
    target = sys.argv[1]
    sys.argv = sys.argv[1:]

    script_dir = os.path.abspath(os.path.dirname(target))
    sys.path.insert(0, script_dir)

    sys.settrace(tracer)
    runpy.run_path(target, run_name="__main__")
    sys.settrace(None)

    for f in tracked_files.values():
        t = TraceAST()
        t.executed_lines = f.executed_lines
        n = t.visit(f.nodes)
        print(ast.unparse(ast.fix_missing_locations(n)))

    print(tracked_files)


if __name__ == "__main__":
    main()
