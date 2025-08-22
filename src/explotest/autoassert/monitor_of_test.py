from sys import monitoring as sm
from types import CodeType
from typing import Any


class TestExecutionMonitor:
    """
    DBC: The `event_analyzer_for_global_state.EventAnalyzer` tool must be released
    with `EventAnalyzer.end_tracking()`. Otherwise, there will still be a lock on `TOOL_ID` which is 3.
    """

    TOOL_ID: int = 3
    TOOL_NAME: str = "explotest_autoassert_test_monitor"
    function_under_test_name: str
    function_under_test_path: str
    retval_found: Any

    def __init__(self, function_under_test_name: str, function_under_test_path: str):
        self.function_under_test_name = function_under_test_name
        self.function_under_test_path = function_under_test_path

    def start_tracking(self):
        print(
            f"==test monitor== starting with fut: {self.function_under_test_name}, fut_path: {self.function_under_test_path}"
        )
        if sm.get_events(self.TOOL_ID):
            raise RuntimeError("The test execution monitor is already running!")
        sm.use_tool_id(self.TOOL_ID, self.TOOL_NAME)
        assert (
            sm.register_callback(self.TOOL_ID, sm.events.PY_RETURN, self.monitor)
            is None
        )
        sm.set_events(self.TOOL_ID, sm.events.PY_RETURN)

    # noinspection PyUnusedLocal
    def monitor(self, code: CodeType, instruction_offset: int, retval: object) -> None:
        # print(code.co_qualname)
        # print(self.test_function_path, self.test_function_name)
        if (
            code.co_qualname == self.function_under_test_name
            and code.co_filename == self.function_under_test_path
        ):
            # breakpoint()
            print("Test function found!")
            self.retval_found = retval
        return None

    def end_tracking(self) -> Any:
        # free tracking
        sm.set_events(self.TOOL_ID, 0)
        sm.register_callback(self.TOOL_ID, sm.events.PY_RETURN, None)
        sm.free_tool_id(self.TOOL_ID)
        return self.retval_found
