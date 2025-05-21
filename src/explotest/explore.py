import functools
import inspect
import os
from _ast import arguments, alias
from pathlib import Path
from typing import Any, cast
import ast
import atexit

import dill  # type: ignore

OUTPUT_FILE_FOLDER = "tests"


# mapping from subroutine names to their call count
call_count: dict[str, int] = dict()


# imports of user defined subroutines-under-test
imports: list[ast.ImportFrom] = []

# generated function definitions from @explore
function_def_asts: list[ast.FunctionDef] = []

import_file = None


def is_primitive(x: Any) -> bool:
    """True iff x is a primitive type (int, float, str, bool) or a list of primitive types."""

    def is_list_of_primitive(lox: list) -> bool:
        return all(is_primitive(item) for item in lox)

    if isinstance(x, list):
        return is_list_of_primitive(x)

    return isinstance(x, (int, float, str, bool))


def emit_tests():
    """Called at the end of program execution to emit the generated tests."""
    import_dill = ast.Import(names=[alias(name="dill")])

    module = ast.Module(
        body=[*imports, import_dill, *function_def_asts], type_ignores=[]
    )
    ast.fix_missing_locations(module)

    # ast.unparse(module)
    print(ast.dump(module, indent=4))

    filename = f"./{OUTPUT_FILE_FOLDER}/test_{import_file}.py"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "w") as f:
        f.write(ast.unparse(module))


atexit.register(emit_tests)


def explore(func):

    @functools.wraps(func)  # preserve docstrings, etc. of original fn
    def wrapper(*args, **kwargs):
        wrapper.counter += 1
        arg_spec = inspect.getfullargspec(func)
        arg_names = arg_spec.args

        assignments = []
        for arg_name, arg_value in zip(arg_names, args):
            if is_primitive(arg_value):
                assignments.append(
                    ast.Assign(
                        targets=[ast.Name(id=arg_name, ctx=ast.Store())],
                        value=ast.Constant(value=arg_value),
                    )
                )
            else:
                assignments.append(
                    ast.Assign(
                        targets=[ast.Name(id=arg_name, ctx=ast.Store())],
                        value=ast.Call(
                            func=ast.Attribute(
                                value=ast.Name(id="dill", ctx=ast.Load()),
                                attr="loads",
                                ctx=ast.Load(),
                            ),
                            # args=[ast.Constant(value=dill.dumps(arg_value))],
                            args=[ast.Constant(value=b"12345")],
                        ),
                    )
                )

        test_func_call = ast.Expr(
            value=ast.Call(
                func=ast.Name(id=func.__qualname__, ctx=ast.Load()),
                args=[ast.Name(id=x, ctx=ast.Load()) for x in arg_names],
            )
        )

        test_func = ast.FunctionDef(
            name=f"test_{func.__qualname__}_{wrapper.counter}",
            args=ast.arguments(),
            body=[*assignments, test_func_call],
        )

        function_def_asts.append(test_func)

        # TODO: kwargs
        # TODO: fix performance bug
        # TODO: fix class name bug
        # TODO: find a better way to find imports
        # TODO: sanitize names for methods (test_foo.bar)
        # TODO: add support for multiple files
        # TODO: write pickled objects to their own file

        # finally, call and return the subroutine-under-test
        return func(*args, **kwargs)

    wrapper.counter = 0
    # FIXME: remove global somehow
    global import_file
    import_file = Path(inspect.getfile(func)).stem
    imports.append(
        ast.ImportFrom(
            module=import_file,
            names=[alias(name=func.__qualname__)],
            level=0,
        )
    )

    return wrapper
