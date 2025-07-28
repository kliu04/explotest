"""
Runs the ExploTest dynamic tracer and AST rewriter pipeline.

Namely:
- Sets a tracing hook to monitor executed lines during program execution.
- Applies pruning and rewriting passes to simplify the AST using both static and dynamic data.

Usage: python -m explotest <target.py>
"""

import ast
import atexit
import copy
import importlib
import inspect
import os
import sys
import types
from pathlib import Path
from typing import Callable

import dill

from explotest.ast_context import ASTContext
from explotest.ast_file import ASTFile
from explotest.ast_importer import Finder
from explotest.ast_pruner import ASTPruner
from explotest.ast_rewriter import ASTRewriterB
from explotest.ast_truncator import ASTTruncator
from explotest.helpers import sanitize_name
from explotest.trace_info import TraceInfo


def is_lib_file(filepath: str) -> bool:
    return any(substring in filepath for substring in ("3.13", ".venv", "<frozen"))


def ddmin(ast_file: ASTFile, arg: inspect.BoundArguments) -> ast.AST:
    seen = set()

    def get_max_lineno(node):
        return max(
            (n.lineno for n in ast.walk(node) if hasattr(n, "lineno")), default=0
        )

    # subset transformer
    class LineFilter(ast.NodeTransformer):
        def __init__(self, begin, end, keep: bool):
            super().__init__()
            self.begin = begin
            self.end = end
            self.keep = keep

        def visit(self, node):
            # if this node has a lineno, decide to keep or drop it
            if hasattr(node, "lineno"):
                in_range = self.begin <= node.lineno <= self.end
                # drop if in range and do not keep, or out of range and keep
                if in_range != self.keep:
                    return None
            return super().visit(node)

    def tracer2(frame, event, arg):
        if event == "call":
            fn = frame.f_globals.get(frame.f_code.co_name) or frame.f_locals.get(
                frame.f_code.co_name
            )
            if hasattr(fn, "__data__"):
                seen_args.append(fn.__data__.args)
        return tracer2

    def run(node_ast):
        seen_args.clear()
        sys.settrace(tracer2)

        ns = dill.loads(dill.dumps(ast_file.d))
        # remove variable store
        for k in list(ns):
            if k not in {"__name__", "__file__", "__builtins__"}:
                del ns[k]
        try:
            sys.call_tracing(
                lambda: exec(compile(node_ast, ast_file.module, "exec"), ns), ()
            )
        except:
            return False
        return arg in seen_args

    def ddmin2(tree: ast.AST, n: int) -> ast.AST:
        # print(ast.unparse(tree))
        total_lines = get_max_lineno(tree)
        if total_lines == 0:
            raise Exception("something bad happened :(")

        tree = ast.parse(ast.unparse(tree))

        # compute chunk boundaries, distributing remainder
        base, rem = divmod(total_lines, n)
        boundaries = []
        start = 1
        for i in range(n):
            size = base + (1 if i < rem else 0)
            end = start + size - 1
            boundaries.append((start, end))
            start = end + 1

        # optimization
        if tuple(boundaries) in seen:
            return tree
        seen.add(tuple(boundaries))

        # reduce to subset
        for begin, end in boundaries:
            sub = LineFilter(begin, end, keep=True).visit(copy.deepcopy(tree))
            if run(sub):
                return ddmin2(sub, 2)

        # reduce to complement
        for begin, end in boundaries:
            comp = LineFilter(begin, end, keep=False).visit(copy.deepcopy(tree))
            if run(comp):
                return ddmin2(comp, max(n - 1, 2))

        # increase granularity
        if n < total_lines:
            return ddmin2(tree, min(total_lines, 2 * n))

        return tree

    seen_args = []

    print(ast.unparse(ddmin2(ast_file.node, 2)))
    return ddmin2(ast_file.node, 2)


def make_tracer(ctx: ASTContext) -> Callable:
    counter = 1

    def _tracer(frame: types.FrameType, event, arg):
        """
        Hooks onto default tracer to add instrumentation for ExploTest.
        :param frame: the current python frame
        :param event: the current event (one-of "line", "call", "return")
        :param arg: currently not used
        :return: must return this object for tracing to work
        """
        filename = frame.f_code.co_filename
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

        elif event == "call":
            # entering a new module always has lineno 0
            if lineno == 0:
                return _tracer
            func_name = frame.f_code.co_name
            func = frame.f_globals.get(func_name) or frame.f_locals.get(func_name)

            if func is None:
                return _tracer

            if hasattr(func, "__data__"):
                nonlocal counter
                # deep copy
                cpy = dill.loads(dill.dumps(ast_file))
                # cut off everything past the call
                output_path = (
                    path.parent / f"test_{sanitize_name(func_name)}_{counter}.py"
                )

                # actually, this should be the AST file of the caller -- not the callee
                # TODO: above
                with open(output_path, "w") as f:
                    # prune ast based on execution paths
                    cpy.transform(ASTPruner())
                    # remove code after the call
                    trace_info: TraceInfo = func.__data__
                    cpy.transform(ASTTruncator(trace_info.lineno))

                    # unpack compound statements
                    cpy.transform(ASTRewriterB())

                    ddmin(ast_file, trace_info.args)
                    sys.settrace(_tracer)

                    f.write(cpy.unparse)
                    f.write("\n\n")

                counter += 1

        return _tracer

    return _tracer


def load_code(root_path: Path, module_name: str, ctx: ASTContext):
    """Load user code, patch function calls."""
    finder = Finder(root_path, ctx)
    try:
        # insert our custom finder into the "meta-path", import the module
        sys.meta_path.insert(0, finder)
        return importlib.import_module(module_name)
    finally:
        sys.meta_path.pop(0)


def main():
    import time

    start = time.time()

    if len(sys.argv) < 2:
        print("Usage: python3 -m explotest <filename>")
        sys.exit(1)

    target = sys.argv[1]
    target_folder = os.path.dirname(target)
    sys.argv = sys.argv[1:]

    script_dir = os.path.abspath(target_folder)
    sys.path.insert(0, script_dir)

    # TODO: make this work for modules
    ctx = ASTContext()
    tracer = make_tracer(ctx)
    sys.settrace(tracer)
    atexit.register(lambda: sys.settrace(None))
    # the next line will run the code and rewriterA
    load_code(Path(script_dir), Path(target).stem, ctx)
    # runpy.run_path(os.path.abspath(target), run_name="__main__")
    sys.settrace(None)

    end = time.time()

    print(end - start)


if __name__ == "__main__":
    main()
