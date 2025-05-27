import ast
import atexit
import functools
import inspect
import os
from _ast import alias
from pathlib import Path
from typing import Self, Final, Optional

import dill  # type: ignore

from explotest import helpers
from explotest.helpers import Mode
from explotest.pickle_reconstructor import PickleReconstructor
from explotest.test_generator import TestGenerator


class TestFunction:
    """Represents a single function-under-test."""

    def __init__(self: Self, name: str, count: int) -> None:
        self.name: Final = name
        self.count: Final = count
        self.ast_node: Optional[ast.FunctionDef] = None

    @property
    def sanitized_name(self):
        return self.name.replace(".", "_")


class TestFileGenerator:
    """Manages test generation for a single source file."""

    def __init__(self: Self, filename, filepath) -> None:
        self.filename: Final = filename
        self.filepath: Final = filepath
        self.imports: list[ast.Import] = []
        # mapping from function name to TestFunction class
        self.test_functions: dict[str, list[TestFunction]] = dict()

    def generate_test_function(self: Self, fn_name: str) -> TestFunction:
        if fn_name in self.test_functions:
            call_count = len(self.test_functions[fn_name]) + 1
            test_func = TestFunction(fn_name, call_count)
            self.test_functions[fn_name].append(test_func)
        else:
            test_func = TestFunction(fn_name, 1)
            self.test_functions[fn_name] = [test_func]
        return test_func

    def emit_tests(self):
        """Generate the complete test file with all collected test functions."""
        import_dill = ast.Import(names=[alias(name="dill")])

        asts = []
        for lis in self.test_functions.values():
            for test_function in lis:
                if test_function.ast_node is not None:
                    asts.append(test_function.ast_node)

        import_statements = [*self.imports, import_dill, *asts]
        module = ast.Module(body=import_statements, type_ignores=[])
        ast.fix_missing_locations(module)

        self._write_test_file(module)

    def _write_test_file(self, module: ast.Module) -> None:
        """Write module to a file."""
        filename = f"{self.filepath}/test_{self.filename}.py"

        with open(filename, "w") as f:
            f.write(ast.unparse(module))


# keeps track of all files
generators: list[TestFileGenerator] = []


def emit_all_tests():
    for generator in generators:
        generator.emit_tests()


# call emit_test when program exits
if not helpers.is_running_under_test():
    atexit.register(emit_all_tests)


def explore(func=None, mode=Mode.RECONSTRUCT):

    def _add_pickled_ast(assignments, pickled_path, parameter):
        assignments.append(
            # with open....
        )

    def _explore(_func):
        if helpers.is_running_under_test():
            return _func

        filepath = Path(inspect.getfile(_func)).parent
        filename = Path(inspect.getfile(_func)).stem
        qualified_name = _func.__qualname__
        file_generator = None
        for generator in generators:
            if generator.filename == filename:
                file_generator = generator
                break
        else:
            file_generator = TestFileGenerator(filename, filepath)
            # NOTE: `@explore` on unreached functions (from main),
            #       do not need to be imported
            file_generator.imports.append(ast.Import(names=[alias(name=filename)]))
            generators.append(file_generator)

        @functools.wraps(_func)  # preserve docstrings, etc. of original fn
        def wrapper(*args, **kwargs):

            os.makedirs(f"{filepath}/pickled", exist_ok=True)
            # clear directory
            for root, _, files in os.walk(f"{filepath}/pickled"):
                for file in files:
                    os.remove(os.path.join(root, file))

            func_signature = inspect.signature(_func)
            bound_args = func_signature.bind(*args, **kwargs)
            bound_args.apply_defaults()

            TestGenerator(qualified_name)

            for parameter, argument in bound_args.arguments.items():
                PickleReconstructor(parameter, argument, filepath)

            # call the function
            test_call = ast.Expr(
                value=ast.Call(
                    func=ast.Name(
                        id=f"{filename}.{test_function.name}", ctx=ast.Load()
                    ),
                    args=[ast.Name(id=x, ctx=ast.Load()) for x in parameters],
                )
            )

            # wrap everything in a function
            test_def_ast = ast.FunctionDef(
                name=f"test_{test_function.sanitized_name}_{test_function.count}",
                args=ast.arguments(
                    posonlyargs=[],
                    args=[],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                ),
                body=[*assignments, test_call],
                decorator_list=[],
                returns=None,
            )

            test_function.ast_node = test_def_ast

            # finally, call and return the function-under-test
            return _func(*args, **kwargs)

        return wrapper

    if func:
        return _explore(func)

    return _explore
