import ast
import atexit
import functools
import inspect
import os
import sys
import uuid
from _ast import alias
from pathlib import Path
from typing import Any, Self, Final

import dill  # type: ignore


class _SUT:
    ast = None

    def __init__(self: Self, name: str, count: int) -> None:
        self.name: Final = name
        self.count: Final = count

    def sanitize_sut_name(self):
        return self.name.replace(".", "_")


class _FileRecorder:
    def __init__(self: Self, filename) -> None:
        self.filename: Final = filename
        self.imports: list[ast.Import] = []
        # mapping from name to suts (1 sut can be called multiple times)
        self.suts: dict[str, list[_SUT]] = dict()

    def generate_sut(self: Self, sut_name: str) -> _SUT:
        _sut = None
        if sut_name in self.suts:
            num_suts = len(self.suts[sut_name])
            _sut = _SUT(sut_name, num_suts + 1)
            self.suts[sut_name].append(_sut)
        else:
            _sut = _SUT(sut_name, 1)
            self.suts[sut_name] = [_sut]
        return _sut

    def emit_tests(self):
        """Called at the end of program execution to emit the generated tests."""
        import_dill = ast.Import(names=[alias(name="dill")])

        asts = []
        for lis in self.suts.values():
            for sut in lis:
                if sut.ast is not None:
                    asts.append(sut.ast)

        module = ast.Module(body=[*self.imports, import_dill, *asts], type_ignores=[])
        ast.fix_missing_locations(module)

        filename = f"./test_{self.filename}.py"

        with open(filename, "w") as f:
            f.write(ast.unparse(module))


recorders: list[_FileRecorder] = []


def emit_testss():
    for recorder in recorders:
        recorder.emit_tests()


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


# call emit_test when program exits
if not is_running_under_test():
    atexit.register(emit_testss)


def explore(func):

    if is_running_under_test():
        return func

    filename = Path(inspect.getfile(func)).stem
    qualified_name = func.__qualname__
    file_recorder = None
    for recorder in recorders:
        if recorder.filename == filename:
            file_recorder = recorder
            break
    else:
        file_recorder = _FileRecorder(filename)
        file_recorder.imports.append(ast.Import(names=[alias(name=filename)]))
        recorders.append(file_recorder)

    @functools.wraps(func)  # preserve docstrings, etc. of original fn
    def wrapper(*args, **kwargs):

        test_sut = file_recorder.generate_sut(qualified_name)
        arg_spec = inspect.getfullargspec(func)
        arg_names = arg_spec.args

        assignments = []
        for arg_name, arg_value in zip(arg_names, args):

            # hard-code primitives
            if is_primitive(arg_value):
                assignments.append(
                    ast.Assign(
                        targets=[ast.Name(id=arg_name, ctx=ast.Store())],
                        value=ast.Constant(value=arg_value),
                    )
                )
            else:
                # create directory for pickled objects, store argument
                os.makedirs("./pickled", exist_ok=True)
                pickled_id = str(uuid.uuid4().hex)[:8]
                pickled_path = f"./pickled/{arg_name}_{pickled_id}.pkl"
                with open(pickled_path, "wb") as f:
                    f.write(dill.dumps(arg_value))

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
                                targets=[ast.Name(id=arg_name, ctx=ast.Store())],
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

        test_call = ast.Expr(
            value=ast.Call(
                func=ast.Name(id=f"{filename}.{test_sut.name}", ctx=ast.Load()),
                args=[ast.Name(id=x, ctx=ast.Load()) for x in arg_names],
            )
        )

        test_def_ast = ast.FunctionDef(
            name=f"test_{test_sut.sanitize_sut_name()}_{test_sut.count}",
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

        test_sut.ast = test_def_ast

        # TODO: kwargs

        # finally, call and return the subroutine-under-test
        return func(*args, **kwargs)

    return wrapper
