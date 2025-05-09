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
    match event:
        case "call":
            frame_info = inspect.getframeinfo(frame)

            # filter out python builtins

            filepath = frame_info.filename
            if (
                frame_info.code_context
                and not is_frozen_file(filepath)
                and not is_stdlib_file(filepath)
                and not is_venv_file(filepath)
            ):
                positions = frame_info.positions
                if positions and positions.lineno > 0:  # type: ignore
                    print(positions, filepath, "CALL")
                    executed_lines.append(*frame_info.code_context)

        case "line":
            frame_info = inspect.getframeinfo(frame)

            # filter out python builtins

            filepath = frame_info.filename
            if (
                frame_info.code_context
                and not is_frozen_file(filepath)
                and not is_stdlib_file(filepath)
                and not is_venv_file(filepath)
            ):
                positions = frame_info.positions
                print(positions, filepath)
                # don't think this is needed
                # if positions:
                #     start_lineno = positions.lineno
                #     end_lineno = positions.end_lineno
                #
                #     if start_lineno is None or end_lineno is None:
                #         print("oh no 2")
                #         raise Exception("oh no 2")
                #
                #     with open(filepath, "r") as f:
                #         lines = f.readlines()
                #         code = lines[start_lineno - 1 : end_lineno]
                #         executed_lines.append(code)
                # print(code)
                # else:
                #     print("oh no")

                executed_lines.append(*frame_info.code_context)
            # filename, lineno, function (function name), code context, index
            # print(frame_info.code_context, frame_info.lineno)

        case "return":
            pass
        case _:
            pass

    return tracer


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 -m explotest <filename>")
        sys.exit(1)

    target = sys.argv[1]
    sys.argv = sys.argv[1:]

    # TODO: fix pathing issues with @explore
    script_dir = os.path.abspath(os.path.dirname(target))
    sys.path.insert(0, script_dir)

    sys.settrace(tracer)
    runpy.run_path(target, run_name="__main__")
    sys.settrace(None)

    target_ast = None
    with open(target, "r") as f:
        target_ast = ast.parse(f.read())
    # parsed_lines = list(map(lambda x: ast.parse(x), executed_lines))
    # print(executed_lines)
    print(ast.dump(target_ast))
    print("".join(executed_lines))


if __name__ == "__main__":
    main()
