import ast
import functools
import inspect
import os
from pathlib import Path
from typing import Literal, Callable

from .helpers import Mode, is_running_under_test, sanitize_name
from .test_generator import TestGenerator


def explore(func: Callable = None, *, mode: Literal["s", "a", "p"] = "p"):

    def _explore(_func):
        # if file is a test file, do nothing
        # (needed to avoid explotest generated code running on itself)
        if is_running_under_test():
            return _func

        # name of function under test
        qualified_name = _func.__qualname__
        file_path = Path(inspect.getsourcefile(_func))
        counter = 1
        _func.__data__ = counter

        # preserve docstrings, etc. of original fn
        @functools.wraps(_func)
        def wrapper(*args, **kwargs):

            # grab formal signature of func
            func_signature = inspect.signature(_func)
            # bind it to given args and kwargs
            bound_args = func_signature.bind(*args, **kwargs)
            # fill in default arguments, if needed
            bound_args.apply_defaults()

            nonlocal counter

            parsed_mode: Mode = Mode.from_string(mode)

            # make pickled directory
            os.makedirs(f"{file_path.parent}/pickled", exist_ok=True)

            if not parsed_mode:
                raise KeyError("Please enter a valid mode.")

            if parsed_mode == Mode.SLICE:
                # TODO: probably a way to either remove/integrate this

                # prev_frame = inspect.currentframe().f_back
                # lineno = prev_frame.f_lineno
                # wrapper.__data__ = TraceInfo(
                #     qualified_name,
                #     Path(prev_frame.f_code.co_filename),
                #     lineno,
                #     bound_args,
                #     counter,
                # )
                #
                #
                # # print(wrapper.__data__)
                #
                # counter += 1

                return _func(*args, **kwargs)

            tg = TestGenerator(qualified_name, file_path, parsed_mode)

            # write test to a file
            with open(
                f"{file_path.parent}/test_{sanitize_name(qualified_name)}_{counter}.py",
                "w",
            ) as f:
                f.write(ast.unparse(tg.generate(bound_args.arguments).ast_node))

            counter += 1

            # finally, call and return the function-under-test
            return _func(*args, **kwargs)

        return wrapper

    # hacky way to allow for both @explore(mode=...) and @explore (defaulting on mode)
    if func:
        return _explore(func)
    return _explore
