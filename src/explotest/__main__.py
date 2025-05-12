import ast
import importlib.util
import inspect
import os
import re
import runpy
import sys
import sysconfig
import types
import typing
from importlib.machinery import ModuleSpec

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
            # I think 0 is just always called as the entry point into a file
            if positions and positions.lineno > 0:  # type: ignore
                # print(positions, filepath, positions.lineno, "CALL")
                executed_lines.append(*frame_info.code_context)

        case "line":
            if positions:
                # print(positions, filepath, positions.lineno)
                executed_lines.append(*frame_info.code_context)

        case "return":
            pass
        case _:
            pass

    return tracer


def traverse_asts(target: str) -> list[ast.AST]:

    def filter_imports(imports: list[str]) -> list[str]:

        # remove builtins
        imports = list(filter(lambda x: not x in sys.stdlib_module_names, imports))
        imports = list(filter(lambda x: not x in sys.builtin_module_names, imports))

        # (mypy cannot detect that modules is not None)

        return imports

    def get_modules_origin(imports: list[str]) -> list[str]:
        modules: typing.List[typing.Optional[ModuleSpec]] = [
            importlib.util.find_spec(x) for x in imports
        ]
        modules_: typing.List[ModuleSpec] = [x for x in modules if x is not None]
        modules__: typing.List[str | None] = [x.origin for x in modules_]

        # FIXME: need a better way to detect user installed packages (perhaps not with pip?)
        modules__ = list(filter(lambda x: not is_venv_file(x), modules__))
        return modules__  # type: ignore

    def flatten(xss: list[list[typing.Any]]) -> list[typing.Any]:
        return [x for xs in xss for x in xs]

    def traverse_asts_inner(t) -> list[ast.AST]:
        with open(t, "r") as f:
            target_ast = ast.parse(f.read(), filename=t)
            imports = []
            for node in ast.walk(target_ast):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)

                elif isinstance(node, ast.ImportFrom):
                    imports.append(node.module)  # type: ignore

                elif isinstance(node, ast.Module):
                    pass
                else:
                    # FIXME: imports do not have to be at the top
                    break

            imports = filter_imports(imports)
            imports = get_modules_origin(imports)

            return flatten(list(map(traverse_asts_inner, imports))) + [target_ast]

    return traverse_asts_inner(target)


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

    # What formats to send to carver?
    # AST optimization (do not load whole file)?
    # can't use lineno/end_lineno trick since multi-line statements exist
    # how to tell which things are executed?

    list(map(lambda x: print(ast.dump(x)), traverse_asts(target)))
    print("".join(executed_lines))


if __name__ == "__main__":
    # print(os.path.dirname(os.path.abspath(__file__)))
    main()
