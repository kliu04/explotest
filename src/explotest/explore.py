import ast
import functools
import inspect
import os
from pathlib import Path
from typing import Any, Callable
from typing import Literal

import openai
from dotenv import load_dotenv

from .autoassert.runner_of_test import TestRunner
from .event_analyzer import EventAnalyzer
from .global_state_detector import find_function_def
from .helpers import Mode, sanitize_name, is_running_under_test
from .reconstructors.argument_reconstructor import ArgumentReconstructor
from .reconstructors.pickle_reconstructor import PickleReconstructor
from .test_builder import TestBuilder


def explore(func: Callable = None, *, mode: Literal["p", "a"] = "p"):
    """Add the @explore annotation to a function to recreate its arguments at runtime."""

    def _explore(_func):
        counter = 0

        # preserve docstrings, etc. of original fn
        @functools.wraps(_func)
        def wrapper(*args, **kwargs) -> Any:

            # if file is a test file, do nothing
            # (needed to avoid explotest generated code running on itself)
            if is_running_under_test():
                return _func

            nonlocal counter
            counter += 1

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

            parsed_mode: Mode = Mode.from_string(mode)

            if not parsed_mode:
                raise KeyError("[ERROR]: Please enter a valid mode ('p' or 'a').")

            match parsed_mode:
                case Mode.PICKLE:
                    reconstructor = PickleReconstructor
                case Mode.ARR:
                    reconstructor = ArgumentReconstructor
                case _:
                    assert False

            load_dotenv()
            eva = EventAnalyzer(
                (_func.__name__, str(fut_path)),
                find_function_def(ast.parse(inspect.getsource(_func)), _func.__name__),
                openai.OpenAI(
                    base_url=r"https://generativelanguage.googleapis.com/v1beta/openai/",
                    api_key=os.getenv("GEMINI_KEY"),
                ),
                model="gemini-2.5-flash-lite-preview-06-17",
            )

            with eva:
                # call and capture the return of the function-under-test
                res: Any = _func(*args, **kwargs)

            llm_result = eva.filtered_vars
            bound_args = {**dict(bound_args.arguments), **llm_result}
            test_builder = TestBuilder(fut_name, fut_path, bound_args, reconstructor)

            if len(llm_result) > 0:
                test_builder.build_mocks(llm_result)

            test = test_builder.build_test()

            # write test to a file
            with open(
                f"{fut_path.parent}/test_{sanitize_name(fut_name)}_{counter}.py",
                "w",
            ) as f:
                os.environ["RUNNING_GENERATED_TEST"] = "true"
                tr = TestRunner(
                    test,
                    str(_func.__name__),
                    str(fut_path),
                    str(fut_path.parent),
                )
                er = tr.run_test()
                # print(er)
                if test:
                    f.write(ast.unparse(test.make_test()))
                del os.environ["RUNNING_GENERATED_TEST"]
            return res

        return wrapper

    # hacky way to allow for both @explore(mode=...) and @explore (defaulting on mode)
    if func:
        return _explore(func)
    return _explore
