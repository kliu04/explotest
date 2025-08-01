# pyright: ignore [reportUnknownVariableType]

import ast
import functools
import inspect
import os
from pathlib import Path

import openai
from dotenv import load_dotenv

from typing import Any

from .pickle_reconstructor import PickleReconstructor
from .global_state_detector import find_global_vars, find_function_def

from .event_analyzer_for_global_state import EventAnalyzer
from .helpers import Mode, is_running_under_test, sanitize_name
from .test_generator import TestGenerator

from .argument_reconstruction_reconstructor import ArgumentReconstructionReconstructor


def explore(func=None, mode=Mode.RECONSTRUCT):

    def _explore(_func):
        # if file is a test file, do nothing
        # (needed to avoid explotest generated code running on itself)
        if is_running_under_test():
            return _func

        # name of function under test
        qualified_name = _func.__qualname__

        file_path = Path(inspect.getsourcefile(_func))

        # make and clear pickled directory
        os.makedirs(f"{file_path.parent}/pickled", exist_ok=True)
        for root, _, files in os.walk(f"{file_path.parent}/pickled"):
            for file in files:
                os.remove(os.path.join(root, file))

        counter = 1

        # preserve docstrings, etc. of original fn
        @functools.wraps(_func)
        def wrapper(*args, **kwargs) -> Any:

            # grab formal signature of func
            func_signature = inspect.signature(_func)
            # bind it to given args and kwargs
            bound_args = func_signature.bind(*args, **kwargs)
            # fill in default arguments, if needed
            bound_args.apply_defaults()

            tg = TestGenerator(qualified_name, file_path, mode)

            nonlocal counter

            counter += 1
            # func_source = inspect.getsource(_func)
            # function_ast_node = None
            # for node in ast.walk(ast.parse(func_source)):
            #     if isinstance(node, ast.FunctionDef) and node.name == _func.__name__:
            #         function_ast_node = node
            #         break
            #

            # finally, call and return the function-under-test
            load_dotenv()
            eva = EventAnalyzer(
                (_func.__name__, str(file_path)),
                [
                    external.name
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
            # print(f"LLM Result: {eva.end_tracking()}")

            mock_generator = (
                ArgumentReconstructionReconstructor(file_path)
                if mode == mode.RECONSTRUCT
                else PickleReconstructor(file_path)
            )

            ptfs = mock_generator.asts(llm_result)
            generated_mocks = [p.ast_node for p in ptfs]

            # write test to a file
            with open(
                f"{file_path.parent}/test_{sanitize_name(qualified_name)}_{counter}.py",
                "w",
            ) as f:
                f.write(
                    ast.unparse(
                        tg.generate(
                            bindings=bound_args.arguments, definitions=generated_mocks
                        ).ast_node
                    )
                )
            return res

        return wrapper

    # hacky way to allow for both @explore(mode=...) and @explore (defaulting on mode)
    if func:
        return _explore(func)
    return _explore
