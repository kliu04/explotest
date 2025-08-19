import os
import uuid
from enum import Enum

# from autoassert import runner_of_test
from typing import Any

collection_t = list | set | dict | tuple
primitive_t = int | float | complex | str | bool | None


class Mode(Enum):
    """The mode that ExploTest runs in; one of pickling, [argument] reconstructing, or slicing."""

    PICKLE = 1
    ARR = 2
    TRACE = 3

    @classmethod
    def from_string(cls, value: str):
        normalized = value.strip().lower()
        aliases = {
            "pickle": cls.PICKLE,
            "p": cls.PICKLE,
            "arr": cls.ARR,
            "a": cls.ARR,
            "trace": cls.TRACE,
            "t": cls.TRACE,
        }
        return aliases.get(normalized)


def is_lib_file(filepath: str) -> bool:
    return any(substring in filepath for substring in ("3.13", ".venv", "<frozen"))


def random_id():
    return uuid.uuid4().hex[:8]


def uniquify(name: str) -> str:
    return f"{name}_{random_id()}"


def sanitize_name(name: str) -> str:
    return name.replace(".", "_")


def is_primitive(x: Any) -> bool:
    """
    True iff x is a primitive type (int, float, str, bool),
    or a collection of primitive types.
    """

    def is_collection_of_primitive(cox: collection_t) -> bool:
        if isinstance(cox, dict):
            # need both keys and values to be primitives
            return is_primitive(cox.keys()) and is_primitive(cox.values())
        return all(is_primitive(item) for item in cox)

    if isinstance(x, collection_t):
        return is_collection_of_primitive(x)

    return isinstance(x, primitive_t)


def is_collection(x: Any) -> bool:
    return isinstance(x, collection_t)


def is_running_under_test():
    """Returns True iff the program-under-test is a test file. (Currently only supports pytest)"""
    return os.getenv("RUNNING_GENERATED_TEST") == "true"
