import ast
import importlib.util
import inspect
import os
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
def is_stdlib_file(filepath: str) -> bool:
    stdlib_path = sysconfig.get_path("stdlib")
    abs_filename = os.path.abspath(filepath)
    abs_stdlib_path = os.path.abspath(stdlib_path)
    return abs_filename.startswith(abs_stdlib_path)


def is_venv_file(filepath: str) -> bool:
    return ".venv" in filepath


def is_frozen_file(filepath: str) -> bool:
    return filepath.startswith("<frozen ")


def tracer(frame: types.FrameType, event: str, arg: typing.Any):
    """
    Hooks onto Python default tracer.
    :param frame:
    :param event:
    :param arg:
    :return: must return this object
    """

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
            # NOTE: I think 0 is just always called as the entry point into a file
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


def traverse_asts(target: str) -> list[ast.AST]:
    """
    Traverse the AST of target, returning the AST of all files imported recursively.
    NOTE: another potential way to do this is by reading all files in the CWD
    :param target:
    :return: list of AST nodes imported
    """

    imported_modules = []

    def filter_imports(imports: list[str]) -> list[str]:

        # remove builtins
        imports = list(filter(lambda x: not x in sys.stdlib_module_names, imports))
        imports = list(filter(lambda x: not x in sys.builtin_module_names, imports))

        return imports

    def get_modules_origin(imports: list[str]) -> list[str]:
        """
        Get file path of imported modules.
        :param imports:
        :return: list of file path of imported modules
        """

        modules: typing.List[ModuleSpec | None] = [
            importlib.util.find_spec(x) for x in imports
        ]
        modules_: list[ModuleSpec] = [x for x in modules if x is not None]
        modules__: list[str | None] = [x.origin for x in modules_]
        modules___: list[str] = [x for x in modules__ if x is not None]

        # FIXME: currently silently ignore errors/Nones here
        # FIXME: need a better way to detect user installed packages (perhaps not with pip?)

        modules___ = list(filter(lambda x: not is_venv_file(x), modules___))
        return modules___

    def flatten(xss: list[list[typing.Any]]) -> list[typing.Any]:
        return [x for xs in xss for x in xs]

    # TODO: may be better to switch to a filename repr of files, rather than their names
    def traverse_asts_inner(t: str) -> list[ast.AST]:

        # prevent infinite recursion (A imports B, B imports A)
        if t in imported_modules:
            return []
        imported_modules.append(t)

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

    # AST optimization (do not load whole file)?
    # can't use lineno/end_lineno trick since multi-line statements exist

    # find imported files
    list(map(lambda x: print(ast.dump(x, indent=4)), traverse_asts(target)))

    # print executed lines
    print("".join(executed_lines))


if __name__ == "__main__":
    main()
