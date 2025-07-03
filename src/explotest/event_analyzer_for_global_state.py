"""
Traces the run-time values of variables in a procedure

Pass 1: Determine the "type" of external variable
Pass 2: Use an LLM to determine whether the external variable should be mocked
Pass 3: Capture and store the value, creating mocks.
"""

from sys import monitoring as sm
from types import CodeType
from typing import Any, Tuple


class EventAnalyzer:
    return_data: list[Tuple[CodeType, int, object]]
    line_data: list[Tuple[CodeType, int]]
    TOOL_ID = 3
    TOOL_NAME = "explotest_mock_tracker"

    def __init__(self):
        self.return_data = []
        self.line_data = []

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
        self.return_data.append((code, instruction_offset, retval))
        return None

    def line_handler(self, code: CodeType, line_number: int) -> Any:
        self.line_data.append((code, line_number))
        return None

    def end_tracking(self):
        for code, instr_offset, retval in self.return_data:
            print(code, instr_offset, retval)
        for code, lineno in self.line_data:
            print(code, lineno)
        sm.free_tool_id(self.TOOL_ID)
