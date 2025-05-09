import ast
import runpy
import sys
import sysconfig
import types
import typing
import os
import inspect
import re

executed_lines = []


# determine if a file is part of the standard library
# E.g., /Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/pkgutil.py
# TODO: check if OS independent
def is_stdlib_file(filepath):
    stdlib_path = sysconfig.get_path("stdlib")
    abs_filename = os.path.abspath(filepath)
    abs_stdlib_path = os.path.abspath(stdlib_path)
    return abs_filename.startswith(abs_stdlib_path)


def is_venv_file(filepath):
    return ".venv" in filepath


def is_frozen_file(filepath):
    frozen = re.compile(r"<frozen .*>")
    return frozen.search(filepath)


def tracer(frame: types.FrameType, event: str, arg: typing.Any):

    frame_info = inspect.getframeinfo(frame)
    filepath = frame_info.filename

    # filter out python builtins
    if (
        (not frame_info.code_context)
        or is_frozen_file(filepath)
        or is_stdlib_file(filepath)
        or is_venv_file(filepath)
    ):
        return tracer

    match event:
        case "call":
            positions = frame_info.positions
            if positions and positions.lineno > 0:  # type: ignore
                print(positions, filepath, "CALL")
                executed_lines.append(*frame_info.code_context)

        case "line":
            positions = frame_info.positions
            print(positions, filepath)
            executed_lines.append(*frame_info.code_context)

        case "return":
            pass
        case _:
            pass

    return tracer


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 -m explotest <filename>")
        sys.exit(1)

    # target is the file to run, shift argv down by 1
    target = sys.argv[1]
    sys.argv = sys.argv[1:]

    # fix pathing issues by adding the target's module to path
    script_dir = os.path.abspath(os.path.dirname(target))
    sys.path.insert(0, script_dir)

    # start custom tracer and run target as main
    sys.settrace(tracer)
    runpy.run_path(target, run_name="__main__")
    sys.settrace(None)

    # generate AST of target
    target_ast = None
    with open(target, "r") as f:
        target_ast = ast.parse(f.read())

    print(ast.dump(target_ast))
    print("".join(executed_lines))


if __name__ == "__main__":
    main()
