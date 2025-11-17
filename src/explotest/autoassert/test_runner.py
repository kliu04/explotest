import os
import sys
from dataclasses import dataclass
from typing import Any

import dill


@dataclass(frozen=True)
class ExecutionResult:
    result_from_run_one: Any
    result_from_run_two: Any


def run_fut_twice(func, args, kwargs) -> ExecutionResult | None:
    """
    Calls and runs the function-under-test twice to check for non determinism.
    :return: tuple of the first and second return values
    """
    old_stdout = sys.stdout
    try:
        # redirect stdout to /dev/null to prevent extra prints from showing up
        f = open(os.devnull, "w")
        sys.stdout = f

        os.environ["RUNNING_GENERATED_TEST"] = "true"

        # save these in case f modifies its arguments
        pickled_args = dill.dumps(args)
        pickled_kwargs = dill.dumps(kwargs)
        ret1 = func(*dill.loads(pickled_args), **dill.loads(pickled_kwargs))
        ret2 = func(*dill.loads(pickled_args), **dill.loads(pickled_kwargs))

        return ExecutionResult(ret1, ret2)
    except Exception:
        return None
    finally:
        sys.stdout = old_stdout
        os.environ.pop("RUNNING_GENERATED_TEST", None)
