import ast
from dataclasses import dataclass
from tempfile import NamedTemporaryFile
from typing import Any

import pytest
from pytest import ExitCode

AUTOASSERT_RUNNING = "AUTOASSERT RUNNING"
from explotest.autoassert.monitor_of_test import TestExecutionMonitor
from explotest.generated_test import GeneratedTest


@dataclass(frozen=True)
class ExecutionResult:
    result_from_run_one: Any
    result_from_run_two: Any


@dataclass
class TestRunner:
    target_test: GeneratedTest
    function_under_test_name: str
    function_under_test_path: str
    output_dir: str

    def run_test(self) -> ExecutionResult | None:
        """
        Writes target_test to a temporary directory, and traces the test execution to grab the variable result.
        Returns None if the test fails (i.e., the test runs into an error).
        """
        with NamedTemporaryFile(
            "w", dir=self.output_dir, prefix="test_", suffix=".py"
        ) as tf:
            tf.write(ast.unparse(self.target_test.to_ast))
            tf.flush()

            tem1 = TestExecutionMonitor(
                self.function_under_test_name, self.function_under_test_path
            )

            tem1.start_tracking()
            retcode_first_run = pytest.main(["-x", tf.name])

            if retcode_first_run != ExitCode.OK:
                return None

            result_from_first_run = tem1.end_tracking()

            tem2 = TestExecutionMonitor(
                self.function_under_test_name, self.function_under_test_path
            )

            tem2.start_tracking()

            retcode_second_run = pytest.main(["-x", tf.name])

            result_from_second_run = tem2.end_tracking()

            if retcode_second_run != ExitCode.OK:
                return None

            return ExecutionResult(result_from_first_run, result_from_second_run)
