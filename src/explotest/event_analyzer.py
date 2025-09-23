"""
Traces the run-time values of variables in a procedure

Pass 1: Determine the "type" of external variable
Pass 2: Use an LLM to determine whether the external variable should be mocked
Pass 3: Capture and store the value, creating mocks.
"""

import ast
import inspect
from sys import monitoring as sm
from types import CodeType
from typing import Any

import openai

from .llm_analysis_pass import LLMAnalyzer


class EventAnalyzer:
    globals_by_frame_id: dict[int, dict[str, object]] = {}
    fn_def: ast.FunctionDef
    TOOL_ID = 3
    TOOL_NAME = "explotest_mock_tracker"
    llm: openai.OpenAI
    model: str
    filtered_vars: dict[str, Any] = {}

    def __init__(
        self,
        proc_filter: tuple[str, str],
        fn_def: ast.FunctionDef,
        llm: openai.OpenAI,
        model: str,
    ):
        """
        :param proc_filter is a tuple containing (in order) 1.: the function name and 2.: the file path of the function that `proc_filter` belongs to.

        """
        self.proc_filter = proc_filter
        self.llm = llm
        self.fn_def = fn_def
        self.model = model

    def __enter__(self):
        if sm.get_events(self.TOOL_ID):
            raise RuntimeError("The event analyzer is already running!")
        sm.use_tool_id(self.TOOL_ID, self.TOOL_NAME)
        assert (
            sm.register_callback(self.TOOL_ID, sm.events.PY_RETURN, self.return_handler)
            is None
        )

        sm.set_events(self.TOOL_ID, sm.events.PY_RETURN)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # TODO: proper exn handling
            return False  # reraise exception

        sm.set_events(self.TOOL_ID, 0)
        sm.register_callback(self.TOOL_ID, sm.events.PY_RETURN, None)
        sm.free_tool_id(self.TOOL_ID)
        # return self.globals_by_frame_id
        for frame_id, var_map in self.globals_by_frame_id.items():
            llm_analysis = LLMAnalyzer(self.llm, self.fn_def, var_map, self.model)
            self.filtered_vars = llm_analysis.filter_mocks()
            break
        return True

    def return_handler(
        self, code: CodeType, instruction_offset: int, retval: object
    ) -> Any:
        # fut may call more functions
        if (
            code.co_qualname == self.proc_filter[0]
            and code.co_filename == self.proc_filter[1]
        ):
            current_frame = inspect.currentframe()
            assert current_frame is not None
            parent_frame = current_frame.f_back
            assert parent_frame is not None
            self.globals_by_frame_id[id(parent_frame)] = {}
            for name, value in parent_frame.f_globals.items():
                if (
                    name not in self.globals_by_frame_id[id(parent_frame)]
                    and not callable(value)
                    and name[0] != "_"
                ):
                    self.globals_by_frame_id[id(parent_frame)][name] = value

        return None
