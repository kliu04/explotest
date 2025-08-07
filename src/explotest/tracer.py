import ast
import copy
import sys
import types
from pathlib import Path
from typing import Callable

from explotest.ast_context import ASTContext
from explotest.ast_pruner import ASTPruner
from explotest.ast_rewriter import ASTRewriterB
from explotest.ast_truncator import ASTTruncator
from explotest.delta_debugger import ddmin
from explotest.equality_oracle import EqualityOracle
from explotest.helpers import is_lib_file, sanitize_name
from explotest.trace_info import TraceInfo


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
                cpy = copy.deepcopy(ast_file)
                output_path = (
                    path.parent / f"test_{sanitize_name(func_name)}_{counter}.py"
                )

                # TODO: actually, this should be the AST file of the caller -- not the callee
                with open(output_path, "w") as f:
                    # prune ast based on execution paths
                    cpy.transform(ASTPruner())
                    # remove code after the call
                    trace_info: TraceInfo = func.__data__

                    # cut off everything past the call
                    cpy.transform(ASTTruncator(trace_info.lineno))

                    # unpack compound statements
                    cpy.transform(ASTRewriterB())

                    print(
                        ast.unparse(ddmin(ast_file, trace_info.args, EqualityOracle()))
                    )
                    sys.settrace(_tracer)

                    f.write(cpy.unparse)
                    f.write("\n\n")

                counter += 1

        return _tracer

    return _tracer
