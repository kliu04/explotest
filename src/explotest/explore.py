import ast
import atexit
import functools
import inspect
import os
import sys
import uuid
from _ast import alias
from pathlib import Path
from typing import Any, Self, Final, Optional

import dill  # type: ignore


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

    def __init__(self: Self, filename) -> None:
        self.filename: Final = filename
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
        filename = f"./test_{self.filename}.py"

        with open(filename, "w") as f:
            f.write(ast.unparse(module))


def is_primitive(x: Any) -> bool:
    """True iff x is a primitive type (int, float, str, bool) or a list of primitive types."""

    def is_list_of_primitive(lox: list) -> bool:
        return all(is_primitive(item) for item in lox)

    if isinstance(x, list):
        return is_list_of_primitive(x)

    return isinstance(x, (int, float, str, bool))


# FIXME: hacky
def is_running_under_test():
    return "pytest" in sys.modules


# keeps track of all files
generators: list[TestFileGenerator] = []


def emit_all_tests():
    for generator in generators:
        generator.emit_tests()


# call emit_test when program exits
if not is_running_under_test():
    atexit.register(emit_all_tests)


def explore(func):
    if is_running_under_test():
        return func

    filename = Path(inspect.getfile(func)).stem
    qualified_name = func.__qualname__
    file_recorder = None
    for recorder in generators:
        if recorder.filename == filename:
            file_recorder = recorder
            break
    else:
        file_recorder = TestFileGenerator(filename)
        # NOTE: `@explore` on unreached functions (from main),
        #       do not need to be imported
        file_recorder.imports.append(ast.Import(names=[alias(name=filename)]))
        generators.append(file_recorder)

    @functools.wraps(func)  # preserve docstrings, etc. of original fn
    def wrapper(*args, **kwargs):

        test_function = file_recorder.generate_test_function(qualified_name)
        os.makedirs("./pickled", exist_ok=True)

        arg_spec = inspect.getfullargspec(func)
        parameters = arg_spec.args
        arguments = []
        # need to figure out which kwargs were used to get varkw
        used_keyword_parameters = set()

        # handle positional parameters
        varargs = []

        if len(parameters) > len(args):
            # too many parameters, not enough args
            # must have default arguments or is a keyword arg
            arguments += list(args)
            for i, missing in enumerate(parameters[len(args) :]):
                if missing in kwargs:
                    arguments.append(kwargs[missing])
                else:
                    arguments.append(arg_spec.defaults[i])
                    used_keyword_parameters.add(missing)

        elif len(parameters) < len(args):
            # need to move rest of args to varargs
            arguments = args[: len(parameters)]
            varargs = args[len(parameters) :]
        elif len(parameters) == len(args):
            arguments = args

        assert len(parameters) == len(arguments)

        # handle keyword parameters
        arguments = list(arguments)
        for keyword_parameter in arg_spec.kwonlyargs:
            if keyword_parameter in kwargs:
                parameters.append(keyword_parameter)
                arguments.append(kwargs[keyword_parameter])
                used_keyword_parameters.add(keyword_parameter)
            else:
                parameters.append(keyword_parameter)
                arguments.append(arg_spec.kwonlydefaults[keyword_parameter])

        assert len(parameters) == len(arguments)
        varkw = {k: v for k, v in kwargs.items() if k not in used_keyword_parameters}

        if arg_spec.varargs is not None:
            parameters.append(arg_spec.varargs)
            arguments.append(varargs)

        if arg_spec.varkw is not None:
            parameters.append(arg_spec.varkw)
            arguments.append(varkw)

        print(parameters, arguments)

        assignments = []
        for parameter, argument in zip(parameters, arguments):

            # hard-code primitives
            if is_primitive(argument):
                assignments.append(
                    ast.Assign(
                        targets=[ast.Name(id=parameter, ctx=ast.Store())],
                        value=ast.Constant(value=argument),
                    )
                )
            else:
                # create directory for pickled objects, store argument
                pickled_id = str(uuid.uuid4().hex)[:8]
                pickled_path = f"./pickled/{parameter}_{pickled_id}.pkl"
                with open(pickled_path, "wb") as f:
                    f.write(dill.dumps(argument))

                assignments.append(
                    # with open....
                    ast.With(
                        items=[
                            ast.withitem(
                                context_expr=ast.Call(
                                    func=ast.Name(id="open", ctx=ast.Load()),
                                    args=[
                                        ast.Constant(value=pickled_path),
                                        ast.Constant(value="rb"),
                                    ],
                                    keywords=[],
                                ),
                                optional_vars=ast.Name(id="f", ctx=ast.Store()),
                            ),
                        ],
                        # load from pickled file
                        body=[
                            ast.Assign(
                                targets=[ast.Name(id=parameter, ctx=ast.Store())],
                                value=ast.Call(
                                    func=ast.Attribute(
                                        value=ast.Name(id="dill", ctx=ast.Load()),
                                        attr="loads",
                                        ctx=ast.Load(),
                                    ),
                                    args=[
                                        ast.Call(
                                            func=ast.Attribute(
                                                value=ast.Name(id="f", ctx=ast.Load()),
                                                attr="read",
                                                ctx=ast.Load(),
                                            )
                                        )
                                    ],
                                    keywords=[],
                                ),
                            ),
                        ],
                    )
                )

        # call the function
        test_call = ast.Expr(
            value=ast.Call(
                func=ast.Name(id=f"{filename}.{test_function.name}", ctx=ast.Load()),
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
        return func(*args, **kwargs)

    return wrapper
