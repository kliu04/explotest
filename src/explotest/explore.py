import ast
import functools
import inspect
from pathlib import Path

from src.explotest.helpers import Mode, is_running_under_test
from src.explotest.test_generator import TestGenerator


def explore(func=None, mode=Mode.PICKLE):

    def _explore(_func):
        # if file is a test file, do nothing
        # (needed to avoid explotest generated code running on itself)
        if is_running_under_test():
            return _func

        # parent directory of file containing func
        filepath = Path(inspect.getfile(_func)).parent

        # name of function under test
        qualified_name = _func.__qualname__

        # preserve docstrings, etc. of original fn
        @functools.wraps(_func)
        def wrapper(*args, **kwargs):

            # grab formal signature of func
            func_signature = inspect.signature(_func)
            # bind it to given args and kwargs
            bound_args = func_signature.bind(*args, **kwargs)
            # fill in default arguments, if needed
            bound_args.apply_defaults()

            tg = TestGenerator(qualified_name, filepath, mode)

            # write test to a file
            with open(f"{filepath}/test_{qualified_name}.py", "w") as f:
                f.write(ast.unparse(tg.generate(bound_args.arguments).ast_node))

            # finally, call and return the function-under-test
            return _func(*args, **kwargs)

        return wrapper

    # hacky way to allow for both @explore(mode=...) and @explore (defaulting on mode)
    if func:
        return _explore(func)
    return _explore
