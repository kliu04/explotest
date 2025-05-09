import ast
import runpy
import sys
import sysconfig
import types
import typing
import os
import inspect
import re


executed_lines: list[str] = []


# determine if a file is part of the standard library
# E.g., /Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/...
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
    positions = frame_info.positions

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
            if positions and positions.lineno > 0:  # type: ignore
                print(positions, filepath, positions.lineno, "CALL")
                executed_lines.append(*frame_info.code_context)

        case "line":
            if positions:
                print(positions, filepath, positions.lineno)
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

    # FIXME?: recursively generate AST of imported modules (?)
    # actually don't need to do this because we can call it :)
    # unless that will mess up explore? not sure TBD
    # since explore can be in multiple lines

    # What formats to send to carver?
    # AST optimization (do not load whole file)?
    # can't use lineno/end_lineno trick since multi-line statements exist
    # how to tell which things are executed?

    # generate AST of target
    target_ast = None
    with open(target, "r") as f:
        target_ast = ast.parse(f.read(), filename=target)

    print(ast.dump(target_ast))
    print("".join(executed_lines))


if __name__ == "__main__":
    main()
