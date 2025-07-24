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
from typing import Any, Tuple

import openai

from explotest.llm_analysis_pass import LLMAnalyzer

LOG = True


class EventAnalyzer:
    return_data: list[Tuple[CodeType, int, object]]
    line_data: list[Tuple[CodeType, int]]
    proc_globals: list[object] = []
    target_names_in_proc: list[str]
    globals_by_frame_id: dict[int, dict[str, object]]
    fn_def: ast.FunctionDef
    TOOL_ID = 3
    TOOL_NAME = "explotest_mock_tracker"
    llm: openai.OpenAI
    model: str

    def __init__(
        self,
        proc_filter: tuple[str, str],
        capture_names_in_proc: list[str],
        fn_def: ast.FunctionDef,
        # oai: openai.OpenAI,
        llm: openai.OpenAI,
        model: str,
    ):
        """
        :param proc_filter is a tuple containing (in order) 1.: the function name and 2.: the file path of the function that `proc_filter` belongs to.

        :param capture_names_in_proc are names we are interested inside the procedure - these have to be names.

        :param oai openai.OpenAI API connection.
        """
        # self.target_names_in_proc = capture_names_in_proc
        self.globals_by_frame_id = {}
        self.proc_filter = proc_filter
        self.return_data = []
        self.line_data = []
        self.llm = llm
        self.fn_def = fn_def
        self.model = model

    def start_tracking(self):
        """
        `end_tracking` must be called some time after `start_tracking` is called.
        """
        if sm.get_events(self.TOOL_ID):
            raise RuntimeError("The event analyzer is already running!")
        sm.use_tool_id(self.TOOL_ID, self.TOOL_NAME)
        assert (
            sm.register_callback(self.TOOL_ID, sm.events.LINE, self.line_handler)
            is None
        )
        assert (
            sm.register_callback(self.TOOL_ID, sm.events.PY_RETURN, self.return_handler)
            is None
        )

        sm.set_events(self.TOOL_ID, sm.events.LINE)
        sm.set_events(self.TOOL_ID, sm.events.PY_RETURN)

    def return_handler(
        self, code: CodeType, instruction_offset: int, retval: object
    ) -> Any:
        # print(self.proc_filter[0])
        if (
            code.co_qualname == self.proc_filter[0]
            and code.co_filename == self.proc_filter[1]
        ):
            # print(self.proc_filter[1], code.co_filename)
            current_frame = inspect.currentframe()
            assert current_frame is not None
            parent_frame = current_frame.f_back
            assert parent_frame is not None
            self.globals_by_frame_id[id(parent_frame)] = {}
            for name, value in parent_frame.f_globals.items():
                # print(f"name: {name}, value: {value}")

                if name not in self.globals_by_frame_id[id(parent_frame)]:
                    # print(f"name: {name}, value: {value}")
                    self.globals_by_frame_id[id(parent_frame)][name] = value
                # breakpoint()
            self.return_data.append((code, instruction_offset, retval))

        return None

    def line_handler(self, code: CodeType, line_number: int) -> Any:
        self.line_data.append((code, line_number))
        return None

    def end_tracking(
        self,
    ) -> dict[str, object] | None:  # pyright: ignore [reportReturnType]
        sm.set_events(self.TOOL_ID, 0)
        sm.register_callback(self.TOOL_ID, sm.events.LINE, None)
        sm.register_callback(self.TOOL_ID, sm.events.PY_RETURN, None)
        sm.free_tool_id(self.TOOL_ID)
        # return self.globals_by_frame_id
        for frame_id, var_map in self.globals_by_frame_id.items():
            llm_analysis = LLMAnalyzer(self.llm, self.fn_def, var_map, self.model)
            print(f"============ FRAME_ID: {frame_id} ============")
            return (
                llm_analysis.filter_mocks()
            )  # return the first instance of the call, we don't care about the rest.
        # just try to recon that
