"""
Used only for slicing!
Sets up tracer that will track every executed line
"""

import ast
import os
import runpy
import sys
import types
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TrackedFile:
    nodes: ast.Module
    executed_lines: set[int] = field(default_factory=set)


tracked_files: dict[Path, TrackedFile] = {}


def is_lib_file(filepath: str) -> bool:
    return any(substring in filepath for substring in ("3.13", ".venv", "<frozen"))


class ASTTracer(ast.NodeTransformer):
    tracked_file: TrackedFile

    @staticmethod
    def _get_all_linenos(nodes):
        """Recursively collect all line numbers from a list of AST nodes"""

        # possible since the child nodes can be pruned, leaving an empty body
        if len(nodes) == 0:
            return set()

        linenos = set()
        for node in nodes:
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
        try:
            super().generic_visit(node)

            body_linenos = self._get_all_linenos(node.body)
            body_was_executed = bool(self.tracked_file.executed_lines & body_linenos)

            # condition is false
            if not body_was_executed:
                return None
            return node
        except ValueError:
            print(ast.dump(node, indent=4))
            raise ValueError

    def visit_FunctionDef(self, node):
        super().generic_visit(node)

        body_linenos = (x for x in range(node.lineno + 1, node.end_lineno + 1))
        body_was_executed = bool(
            self.tracked_file.executed_lines.intersection(body_linenos)
        )
        # TODO: change this to just pass ?
        if not body_was_executed:
            return None
        return node

    def visit_Try(self, node):
        super().generic_visit(node)
        handler_linenos = self._get_all_linenos(node.handlers)
        handler_was_executed = bool(
            self.tracked_file.executed_lines.intersection(handler_linenos)
        )

        if not handler_was_executed:
            if node.orelse or node.finalbody:
                # change catching exception to pass
                return ast.Try(
                    node.body,
                    [
                        ast.ExceptHandler(
                            type=ast.Name(id="Exception", ctx=ast.Load()),
                            name="e",
                            body=[ast.Pass()],
                        )
                    ],
                    node.orelse,
                    node.finalbody,
                )
            else:
                return node.body

        # remove else since exception was raised
        return ast.Try(
            node.body,
            node.handlers,
            None,
            node.finalbody,
        )


class ASTRewriter(ast.NodeTransformer):

    queue: list[tuple[list[ast.AST], ast.AST]]

    def __init__(self):
        super().__init__()
        self.queue = []

    def visit_If(self, node):
        self.generic_visit(node)

        if not node.orelse:
            node.orelse = [ast.Pass()]

        return node

    def visit_Assign(self, node: ast.Assign):
        """
        unpacks tuple assignments and ifexp assignments
        """
        self.generic_visit(node)

        # check for a tuple unpacking assignment
        if (
            isinstance(node.targets[0], ast.Tuple)
            and isinstance(node.value, ast.Tuple)
            and len(node.targets[0].elts) == len(node.value.elts)
        ):
            # generate one assignment per target-value pair
            self.queue.append(
                (
                    [
                        ast.Assign(targets=[target], value=value)
                        for target, value in zip(node.targets[0].elts, node.value.elts)
                    ],
                    node,
                )
            )
            return None

        if isinstance(node.value, ast.IfExp):
            return ast.If(
                node.value.test,
                [ast.Assign(targets=[node.targets[0]], value=node.value.body)],
                [ast.Assign(targets=[node.targets[0]], value=node.value.orelse)],
            )

        return node

    def visit_Call(self, node):
        """
        unpack expressions in call contexts
        """
        self.generic_visit(node)
        self.queue.append(
            (
                [
                    ast.Assign(
                        targets=[ast.Name(id=f"temp_{i}", ctx=ast.Store())],
                        value=arg.value if isinstance(arg, ast.Starred) else arg,
                    )
                    for i, arg in enumerate(node.args)
                ],
                node,
            )
        )
        node.args = [
            (
                ast.Starred(value=ast.Name(id=f"temp_{i}", ctx=ast.Load()), ctx=arg.ctx)
                if isinstance(arg, ast.Starred)
                else ast.Name(id=f"temp_{i}", ctx=ast.Load())
            )
            for i, arg in enumerate(node.args)
        ]

        return node

    def visit_Subscript(self, node):
        self.generic_visit(node)

        if isinstance(node.slice, ast.Slice):
            self.queue.append(
                (
                    [
                        ast.Assign(
                            targets=[ast.Name(id="temp_0", ctx=ast.Store())],
                            value=node.slice.lower,
                        ),
                        ast.Assign(
                            targets=[ast.Name(id="temp_1", ctx=ast.Store())],
                            value=node.slice.upper,
                        ),
                    ],
                    node,
                )
            )

            # noinspection PyArgumentList
            node.slice = ast.Slice(
                ast.Name(id="temp_0", ctx=ast.Load()),
                ast.Name(id="temp_1", ctx=ast.Load()),
            )

            return node
        else:
            self.queue.append(
                (
                    [
                        ast.Assign(
                            targets=[ast.Name(id="temp", ctx=ast.Store())],
                            value=node.slice,
                        )
                    ],
                    node,
                )
            )
            node.slice = ast.Name("temp", ctx=ast.Load())
            return node

    def rewrite(self, node):
        node.parent = None
        for n in ast.walk(node):
            for child in ast.iter_child_nodes(n):
                child.parent = n

        new_node = self.visit(node)
        for assignments, n in self.queue:
            ASTRewriter.insert_assignments(assignments, n)
        ast.fix_missing_locations(new_node)
        self.queue.clear()
        return new_node

    @staticmethod
    def insert_assignments(assignments, node):
        parent = node.parent
        # Walk up to find a parent that has a "body" list containing the node
        while parent:
            for attr in ["body", "orelse", "finalbody"]:
                if hasattr(parent, attr):
                    body = getattr(parent, attr)
                    if isinstance(body, list) and node.parent in body:
                        index = body.index(node.parent)
                        body[index:index] = assignments  # insert before
                        return
            parent = parent.parent


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
    # FIXME: this
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
            t = TrackedFile(tree)
            tracked_files[path] = t

        if event == "line":
            t.executed_lines.add(lineno)
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
        rewriter = ASTRewriter()
        nodes = rewriter.rewrite(tf.nodes)
        nodes = ast.fix_missing_locations(nodes)

        asttracer = ASTTracer()
        asttracer.tracked_file = tf
        nodes = asttracer.visit(nodes)
        nodes = ast.fix_missing_locations(nodes)

        # Create new module with flattened statements
        # new_tree = ast.Module(body=new_statements, type_ignores=[])
        print(ast.unparse(nodes))


if __name__ == "__main__":
    main()
