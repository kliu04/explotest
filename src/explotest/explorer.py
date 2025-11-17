import ast
import functools
import inspect
import sys
from pathlib import Path
from typing import Any, Callable
from typing import Literal

import dill

from .autoassert import test_runner
from .autoassert.autoassert import (
    AssertionGenerator,
)
from .helpers import Mode, sanitize_name, is_running_under_test
from .reconstructors.argument_reconstructor import ArgumentReconstructor
from .reconstructors.pickle_reconstructor import PickleReconstructor
from .test_builder import TestBuilder

record = False
dill.settings["recurse"] = True


def explotest_record():
    global record
    record = True


def explore(
    func: Callable | None = None,
    *,
    mode: Literal["p", "a"] = "p",
    explicit_record: bool = False,
) -> Callable:
    """Add the @explore annotation to a function to recreate its arguments at runtime."""

    def _explore(_func):
        counter = 0

        # preserve docstrings, etc. of original fn
        @functools.wraps(_func)
        def wrapper(*args, **kwargs) -> Any:
            global record
            record = False

            # if file is a test file, do nothing
            # (needed to avoid explotest generated code running on itself)
            if is_running_under_test():
                return _func(*args, **kwargs)

            nonlocal counter
            counter += 1

            # fix depth at current recursion depth (otherwise all counters will be at the last one)
            depth = counter

            fut_name = _func.__qualname__
            source = inspect.getsourcefile(_func)

            if source is None:
                raise FileNotFoundError(
                    f"[ERROR]: ExploTest cannot find the source file of the function {fut_name}."
                )
            fut_path = Path(source)

            # grab formal signature of func
            fut_signature = inspect.signature(_func)
            # bind it to given args and kwargs
            bound_args = fut_signature.bind(*args, **kwargs)
            # fill in default arguments, if needed
            bound_args.apply_defaults()

            parsed_mode = Mode.from_string(mode)

            if not parsed_mode:
                raise KeyError("[ERROR]: Please enter a valid mode ('p' or 'a').")

            match parsed_mode:
                case Mode.PICKLE:
                    reconstructor = PickleReconstructor(fut_path)
                case Mode.ARR:
                    reconstructor = ArgumentReconstructor(fut_path, PickleReconstructor)
                case _:
                    assert False

            bound_args = {**dict(bound_args.arguments)}
            test_builder = TestBuilder(
                fut_path,
                fut_name,
                bound_args,
            )

            test_builder.build_imports(
                getattr(sys.modules[_func.__module__], "__package__", None)
            ).build_fixtures(reconstructor).build_act_phase(fut_signature)
            test_builder.build_mocks({}, reconstructor)

            # this has to be below where we save the arguments to avoid mutation affecting the saved
            # arguments
            res: Any = _func(*args, **kwargs)

            if explicit_record and not record:
                return res

            execution_result = test_runner.run_fut_twice(_func, args, kwargs)
            if execution_result:
                assertion_generator = AssertionGenerator()
                assertion_generator.determine_assertion(execution_result)
                assertion_result = assertion_generator.generate_assertion(res, fut_path)
                test_builder.build_assertions(assertion_result)

            meta_test = test_builder.get_meta_test()

            # write test to a file
            if meta_test:
                with open(
                    f"{fut_path.parent}/test_{sanitize_name(fut_name)}_{depth}.py",
                    "w",
                ) as f:
                    f.write(ast.unparse(meta_test.make_test()))
            else:
                print(
                    f"ExploTest failed creating a unit test for the function {fut_name}."
                )
            return res

        return wrapper

    # hacky way to allow for both @explore(mode=...) and @explore (defaulting on mode)
    if func:
        return _explore(func)
    return _explore
