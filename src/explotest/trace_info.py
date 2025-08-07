import inspect
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TraceInfo:
    """
    :param function_name: name of the function
    :param caller_file: path of where the function was called
    :param lineno: line number of where the function was called
    :param args: binding of parameters to arguments
    :param iteration: number of times this function was called
    """
    function_name: str
    caller_file: Path
    lineno: int
    args: inspect.BoundArguments
    iteration: int
