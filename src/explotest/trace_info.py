import inspect
from dataclasses import dataclass


@dataclass(frozen=True)
class TraceInfo:
    lineno: int
    args: inspect.BoundArguments
