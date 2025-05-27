import sys
from enum import Enum
from typing import Any


class Mode(Enum):
    """The mode that ExploTest runs in; one of pickling, [argument] reconstructing, or slicing."""

    PICKLE = 1
    RECONSTRUCT = 2
    SLICE = 3


def is_primitive(x: Any) -> bool:
    """True iff x is a primitive type (int, float, str, bool) or a list of primitive types."""

    # FIXME: support sets, dicts of primitives

    def is_list_of_primitive(lox: list) -> bool:
        return all(is_primitive(item) for item in lox)

    if isinstance(x, list):
        return is_list_of_primitive(x)

    return isinstance(x, (int, float, str, bool))


def is_running_under_test():
    return "pytest" in sys.modules
