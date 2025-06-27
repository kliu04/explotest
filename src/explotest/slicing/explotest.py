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


tracked_files: dict[Path, TrackedFile] = {}


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


class ASTTracer(ast.NodeTransformer):
    tracked_file: TrackedFile

    @staticmethod
    def _get_all_linenos(nodes):
        """Recursively collect all line numbers from a list of AST nodes"""
        linenos = set()
        for node in nodes:
            if hasattr(node, "lineno"):
                linenos.add(node.lineno)
            # Recursively collect from all child nodes
            for child in ast.walk(node):
                if hasattr(child, "lineno"):
                    linenos.add(child.lineno)

        return set(x for x in range(min(linenos), max(linenos) + 1))

    def visit_If(self, node):

        # visit children recursively
        super().generic_visit(node)

        body_linenos = self._get_all_linenos(node.body)
        body_was_executed = bool(
            self.tracked_file.executed_lines.intersection(body_linenos)
        )

        if body_was_executed:
            return node.body
        else:
            return node.orelse

    def visit_For(self, node):

        super().generic_visit(node)

        body_linenos = self._get_all_linenos(node.body)
        body_was_executed = bool(
            self.tracked_file.executed_lines.intersection(body_linenos)
        )

        # condition is false
        if not body_was_executed:
            return None
        return node

    def visit_FunctionDef(self, node):
        super().generic_visit(node)

        body_linenos = (x for x in range(node.lineno + 1, node.end_lineno + 1))
        body_was_executed = bool(
            self.tracked_file.executed_lines.intersection(body_linenos)
        )
        if not body_was_executed:
            return None
        return node


class ASTFlattener(ast.NodeTransformer):

    # unpack x, y, z = a, b, c into multiple lines
    def visit_Assign(self, node):
        self.generic_visit(node)

        # check for a tuple unpacking assignment
        if (
            isinstance(node.targets[0], ast.Tuple)
            and isinstance(node.value, ast.Tuple)
            and len(node.targets[0].elts) == len(node.value.elts)
        ):
            # generate one assignment per target-value pair
            new_nodes = [
                ast.Assign(targets=[target], value=value)
                for target, value in zip(node.targets[0].elts, node.value.elts)
            ]
            return new_nodes

        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        new_nodes = []
        return node

    def visit_Subscript(self, node):
        self.generic_visit(node)
        return node


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
        t = ASTTracer()
        t.tracked_file = f
        # print(ast.dump(f.nodes, indent=4))
        n = t.visit(f.nodes)
        print(ast.unparse(ast.fix_missing_locations(n)))


if __name__ == "__main__":
    main()
