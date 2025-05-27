import functools
import inspect
import os
from pathlib import Path

from explotest import Mode, helpers
from explotest.test_generator import TestGenerator


def explore(func=None, mode=Mode.RECONSTRUCT):

    def _explore(_func):
        if helpers.is_running_under_test():
            return _func

        filepath = Path(inspect.getfile(_func)).parent
        qualified_name = _func.__qualname__

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

            tg = TestGenerator(qualified_name, mode)
            tg.generate(bound_args.arguments)

            # finally, call and return the function-under-test
            return _func(*args, **kwargs)

        return wrapper

    # hacky way to allow for both @explore(mode=...) and @explore (defaulting on mode)
    if func:
        return _explore(func)
    return _explore
