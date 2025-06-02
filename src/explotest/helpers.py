import sys
import uuid
from enum import Enum
from typing import Any

collection_t = list | set | dict | tuple


class Mode(Enum):
    """The mode that ExploTest runs in; one of pickling, [argument] reconstructing, or slicing."""

    PICKLE = 1
    RECONSTRUCT = 2
    SLICE = 3


def random_id():
    return uuid.uuid4().hex[:8]


def sanitize_name(name: str) -> str:
    return name.replace(".", "_")


def is_primitive(x: Any) -> bool:
    """True iff x is a primitive type (int, float, str, bool) or a list of primitive types."""

    primitive_t = int | float | str | bool | bytearray | None

    def is_collection_of_primitive(cox: collection_t) -> bool:
        if isinstance(cox, dict):
            # need both keys and values to be primitives
            return all(is_primitive(item) for item in cox) and is_primitive(
                cox.values()
            )
        return all(is_primitive(item) for item in cox)

    if isinstance(x, collection_t):
        return is_collection_of_primitive(x)

    return isinstance(x, primitive_t)


def is_collection(x: Any) -> bool:
    return isinstance(x, collection_t)


def is_running_under_test():
    """Returns True iff the program-under-test is a test file. (Currently only supports pytest)"""
    return "pytest" in sys.modules
