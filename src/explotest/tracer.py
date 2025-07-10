"""
Used only for slicing!
Sets up tracer that will track every executed line
"""

import ast
import bisect
import os
import runpy
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import cast


@dataclass
class TrackedFile:
    nodes: ast.Module
    abstract_line_numbers: set[int]
    concrete_line_numbers: list[int]

    def __init__(self, nodes):
        self.nodes = nodes
        self.abstract_line_numbers = set()
        self.concrete_line_numbers = list()


tracked_files: dict[Path, TrackedFile] = {}


def is_lib_file(filepath: str) -> bool:
    return any(substring in filepath for substring in ("3.13", ".venv", "<frozen"))


class ASTTracer(ast.NodeTransformer):
    tracked_file: TrackedFile

    def __init__(self, tracked_file: TrackedFile):
        self.tracked_file = tracked_file

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
            self.tracked_file.abstract_line_numbers.intersection(body_linenos)
        )
        else_linenos = self._get_all_linenos(node.orelse)
        else_was_executed = bool(
            self.tracked_file.abstract_line_numbers.intersection(else_linenos)
        )

        if body_was_executed and else_was_executed:
            # both were executed, say in a loop
            return node
        elif body_was_executed:
            # only the body was executed
            return node.body
        else:
            # only else was executed
            return node.orelse

    def visit_For(self, node):
        try:
            super().generic_visit(node)

            body_linenos = self._get_all_linenos(node.body)
            body_was_executed = bool(
                self.tracked_file.abstract_line_numbers & body_linenos
            )

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
            self.tracked_file.abstract_line_numbers.intersection(body_linenos)
        )
        # TODO: change this to just pass ?
        if not body_was_executed:
            return None
        return node

    def visit_Try(self, node):
        super().generic_visit(node)
        handler_linenos = self._get_all_linenos(node.handlers)
        handler_was_executed = bool(
            self.tracked_file.abstract_line_numbers.intersection(handler_linenos)
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
            [],
            node.finalbody,
        )


class ASTRewriter(ast.NodeTransformer):

    queue: list[tuple[list[ast.AST], ast.AST]]
    tracked_file: TrackedFile

    def __init__(self, tracked_file: TrackedFile):
        super().__init__()
        self.queue = []
        self.tracked_file = tracked_file
        self.tracked_file.concrete_line_numbers = list(
            tracked_file.abstract_line_numbers
        )
        self.tracked_file.concrete_line_numbers.sort()

    def modify_lines(self, pivot: int, num: int):
        """
        :param pivot: Increase CLN for linenos after pivot
        :param num:   Number to increase CLN by
        :return:      None
        """
        idx = bisect.bisect_right(self.tracked_file.concrete_line_numbers, pivot)
        for i in range(idx, len(self.tracked_file.concrete_line_numbers)):
            self.tracked_file.concrete_line_numbers[i] += num

    def visit_If(self, node):
        self.generic_visit(node)

        if not node.orelse:
            node.orelse = [ast.Pass()]
            self.modify_lines(node.end_lineno, 2)
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
            old_num_linenos = node.end_lineno - node.lineno + 1
            tv = list(zip(node.targets[0].elts, node.value.elts))
            new_num_linenos = len(tv)
            t, v = tv.pop()
            assign = ast.Assign(targets=[t], value=v)
            assign.parent = node.parent
            # generate one assignment per target-value pair
            self.queue.append(
                (
                    [ast.Assign(targets=[target], value=value) for target, value in tv],
                    assign,
                )
            )
            self.modify_lines(node.end_lineno, new_num_linenos - old_num_linenos)

            return assign

        if isinstance(node.value, ast.IfExp):
            self.modify_lines(node.end_lineno, 100000)
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

        lis = []
        for i, arg in enumerate(node.args):
            if ASTRewriter.is_simple(arg):
                continue
            elif isinstance(arg, ast.Starred):
                lis.append(
                    ast.Assign(
                        targets=[ast.Name(id=f"temp_{i}", ctx=ast.Store())],
                        value=arg.value,
                    )
                )
            else:
                lis.append(
                    ast.Assign(
                        targets=[ast.Name(id=f"temp_{i}", ctx=ast.Store())], value=arg
                    )
                )
        self.queue.append((lis, node))

        lis = []
        for i, arg in enumerate(node.args):
            if ASTRewriter.is_simple(arg):
                lis.append(arg)
            elif isinstance(arg, ast.Starred):
                lis.append(
                    ast.Starred(
                        value=ast.Name(id=f"temp_{i}", ctx=ast.Load()), ctx=arg.ctx
                    )
                )
            else:
                lis.append(ast.Name(id=f"temp_{i}", ctx=ast.Load()))

        node.args = lis

        return node

    @staticmethod
    def is_simple(arg):
        return isinstance(arg, (ast.Constant, ast.Name))

    def visit_Subscript(self, node):
        self.generic_visit(node)

        if isinstance(node.slice, ast.Slice):

            assignments = []
            slice_kwargs = {}

            if node.slice.lower:
                if not ASTRewriter.is_simple(node.slice.lower):
                    assignments.append(
                        ast.Assign(
                            targets=[ast.Name(id="temp_0", ctx=ast.Store())],
                            value=node.slice.lower,
                        )
                    )
                    slice_kwargs["lower"] = ast.Name(id="temp_0", ctx=ast.Load())
                else:
                    slice_kwargs["lower"] = node.slice.lower

            if node.slice.upper:
                if not ASTRewriter.is_simple(node.slice.upper):
                    temp_name = "temp_1" if node.slice.lower else "temp_0"
                    assignments.append(
                        ast.Assign(
                            targets=[ast.Name(id=temp_name, ctx=ast.Store())],
                            value=node.slice.upper,
                        )
                    )
                    slice_kwargs["upper"] = ast.Name(id=temp_name, ctx=ast.Load())
                else:
                    slice_kwargs["upper"] = node.slice.upper

            if assignments:
                self.queue.append((assignments, node))
                node.slice = ast.Slice(**slice_kwargs)

            return node
        elif ASTRewriter.is_simple(node.slice):
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

    def visit_FunctionDef(self, node):
        self.generic_visit(node)

        # remove docstrings
        if isinstance(node.body[0], ast.Expr):
            expr = cast(ast.Expr, node.body[0])
            if isinstance(expr.value, ast.Constant):
                potential_docstring = expr.value.value
                if type(potential_docstring) is str:
                    node.body = node.body[1:]
                    if not node.body:
                        # potentially, a function could only have a docstring and nothing else (god knows why)
                        node.body = [ast.Pass()]

        return node

    def rewrite(self):
        node = self.tracked_file.nodes
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

        def ancestor_in_body(n, body):
            if n is None:
                return None
            if n in body:
                return n, body
            return ancestor_in_body(n.parent, body)

        parent = node.parent
        # walk up to find a parent that has a "body" list containing the node

        while parent:
            for attr in ["body", "orelse", "finalbody"]:
                if hasattr(parent, attr):
                    body = getattr(parent, attr)
                    if isinstance(body, list) and (t := ancestor_in_body(node, body)):
                        index = t[1].index(t[0])
                        body[index:index] = assignments  # insert before
                        return
            parent = parent.parent

        raise RuntimeError("Cannot find place to insert assignments.")


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
            t.abstract_line_numbers.add(lineno)
        # t.executed_lines.add(lineno)
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

        print(ast.unparse(nodes))

        asttracer = ASTTracer(tf)
        nodes = asttracer.visit(nodes)
        nodes = ast.fix_missing_locations(nodes)

        print(tf.abstract_line_numbers)

        # Create new module with flattened statements
        # new_tree = ast.Module(body=new_statements, type_ignores=[])
        print(ast.unparse(nodes))


if __name__ == "__main__":
    main()
