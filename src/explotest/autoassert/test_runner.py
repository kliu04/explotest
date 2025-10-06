from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExecutionResult:
    result_from_run_one: Any
    result_from_run_two: Any


def run_fut_twice(func, args, kwargs) -> ExecutionResult | None:
    """
    Calls and runs the function-under-test twice to check for non determinism.
    :return: tuple of the first and second return values
    """
    try:
        ret1 = func(*args, **kwargs)
        ret2 = func(*args, **kwargs)
        return ExecutionResult(ret1, ret2)
    except Exception:
        return None
