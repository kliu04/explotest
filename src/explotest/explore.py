# pyright: ignore [reportUnknownVariableType]

import ast
import functools
import inspect
import os
from pathlib import Path
from typing import Any, Callable
from typing import Literal

import openai
from dotenv import load_dotenv

from .argument_reconstructor import ArgumentReconstructor
from .autoassert.runner_of_test import TestRunner
from .event_analyzer_for_global_state import EventAnalyzer
from .global_state_detector import find_global_vars, find_function_def
from .helpers import Mode, sanitize_name, is_running_under_test
from .pickle_reconstructor import PickleReconstructor
from .test_generator import TestGenerator


def explore(func: Callable = None, *, mode: Literal["p", "a"] = "p"):

    def _explore(_func):

        counter = 1



        # preserve docstrings, etc. of original fn
        @functools.wraps(_func)
        def wrapper(*args, **kwargs) -> Any:

            # if file is a test file, do nothing
            # (needed to avoid explotest generated code running on itself)
            if is_running_under_test():
                return _func

            # name of function under test
            qualified_name = _func.__qualname__
            file_path = Path(inspect.getsourcefile(_func))

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

            # if parsed_mode == Mode.TRACE:
            #     # TODO: probably a way to either remove/integrate this
            #     return _func(*args, **kwargs)
            pickle_reconstructor = PickleReconstructor(file_path)
            arr_reconstructor = ArgumentReconstructor(file_path, pickle_reconstructor)

            match parsed_mode:
                case Mode.PICKLE:
                    reconstructor = pickle_reconstructor
                case Mode.ARR:
                    reconstructor = arr_reconstructor
                case _:
                    assert False

            tg = TestGenerator(qualified_name, file_path, reconstructor)

            counter += 1

            # finally, call and return the function-under-test
            load_dotenv()
            eva = EventAnalyzer(
                (_func.__name__, str(file_path)),
                [
                    external.name  # external name is dead code
                    for external in find_global_vars(
                        ast.parse(open(str(file_path)).read()), _func.__name__
                    )
                ],
                find_function_def(ast.parse(inspect.getsource(_func)), _func.__name__),
                openai.OpenAI(
                    base_url=r"https://generativelanguage.googleapis.com/v1beta/openai/",
                    api_key=os.getenv("GEMINI_KEY"),
                ),
                model="gemini-2.5-flash-lite-preview-06-17",
            )
            eva.start_tracking()
            res: Any = _func(*args, **kwargs)
            llm_result = eva.end_tracking()

            mock_generator = (
                ArgumentReconstructor(file_path)
                if parsed_mode == Mode.ARR
                else PickleReconstructor(file_path)
            )

            ptfs = mock_generator.asts(llm_result)
            generated_mocks = [p.ast_node for p in ptfs]

            mock_setup = TestGenerator.create_mocks(
                {fixture.parameter: fixture for fixture in ptfs}
            )

            # write test to a file
            with open(
                f"{file_path.parent}/test_{sanitize_name(qualified_name)}_{counter}.py",
                "w",
            ) as f:
                generated_test = tg.generate(
                    bindings=bound_args.arguments,
                    definitions=generated_mocks + [mock_setup],
                )
                os.environ["RUNNING_GENERATED_TEST"] = "true"
                tr = TestRunner(
                    generated_test,
                    str(_func.__name__),
                    str(file_path),
                    str(file_path.parent),
                )
                er = tr.run_test()
                print(er)
                del os.environ["RUNNING_GENERATED_TEST"]
                f.write(ast.unparse(generated_test.to_ast))
            return res

        return wrapper

    # hacky way to allow for both @explore(mode=...) and @explore (defaulting on mode)
    if func:
        return _explore(func)
    return _explore
