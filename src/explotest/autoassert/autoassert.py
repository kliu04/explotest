"""
AutoAssert style assertion generator for ExploTest
"""

import ast
from dataclasses import dataclass
from enum import Enum
from typing import Any

import dill

from explotest.autoassert.test_runner import ExecutionResult
from explotest.meta_fixture import MetaFixture
from explotest.reconstructors.argument_reconstructor import ArgumentReconstructor
from explotest.reconstructors.pickle_reconstructor import PickleReconstructor


class AssertionToGenerate(Enum):
    NULL = 0
    NON_NULL = 1
    TYPE = 2
    LENGTH = 3
    REPR = 4
    PICKLE = 5
    ARR = 6
    NONE = -1


@dataclass
class AssertionResult:
    fixtures: list[MetaFixture]
    assertions: list[ast.Assert]


def has_custom_repr(raw: Any) -> bool:
    cls = getattr(raw, "__class__", False)
    if not cls:
        return False
    for base in cls.__mro__:
        if "__repr__" in base.__dict__:
            return base is not object
    return False


class AssertionGenerator:

    assertion_to_generate: AssertionToGenerate | None = None
    type_data: str | None = None

    def determine_assertion(self, er: ExecutionResult) -> None:
        """
        :param er: Result of two runs of the function-under-test
        :return: Strongest kind of assertion to generate
        """
        if er.result_from_run_one is None and er.result_from_run_two is None:
            self.assertion_to_generate = AssertionToGenerate.NULL
            return

        if er.result_from_run_one == er.result_from_run_two:
            if ArgumentReconstructor.is_reconstructible(er.result_from_run_one):
                self.assertion_to_generate = AssertionToGenerate.ARR
            else:
                try:
                    dill.dumps(er.result_from_run_one)  # try to serialize...
                    # success if we reach this block
                    self.assertion_to_generate = AssertionToGenerate.PICKLE
                except Exception:
                    if has_custom_repr(er.result_from_run_one):
                        self.assertion_to_generate = AssertionToGenerate.REPR
                    else:
                        # same type
                        self.assertion_to_generate = AssertionToGenerate.TYPE
                        # I'm really sorry for this affront against programming
                        self.type_data = type(er.result_from_run_one).__name__
        elif type(er.result_from_run_one) is type(er.result_from_run_two):
            # if they're the same type, let's see if it has a __len__ quality
            if getattr(er.result_from_run_one, "__len__", False) and len(
                er.result_from_run_one
            ) == len(
                er.result_from_run_two
            ):  # if the lengths are equal, let's use length
                self.assertion_to_generate = AssertionToGenerate.LENGTH
            else:
                self.assertion_to_generate = AssertionToGenerate.TYPE
                self.type_data = type(er.result_from_run_one).__name__
        else:
            # this means they have different types, which also captures the case where one object is none and the
            # other is not none. there's no meaningful assertion to generate between two objects of *different* types.
            self.assertion_to_generate = AssertionToGenerate.NONE

    def generate_assertion(
        self,
        value: Any,
        fut_path,
        value_name: str = "return_value",
    ) -> AssertionResult:
        match self.assertion_to_generate:
            case None:
                raise RuntimeError()
            case AssertionToGenerate.NULL:
                return AssertionResult(
                    [],
                    [
                        ast.Assert(
                            test=ast.Compare(
                                left=ast.Name(id=value_name, ctx=ast.Load()),
                                ops=[ast.Is()],
                                comparators=[ast.Constant(value=None)],
                            )
                        )
                    ],
                )
            case AssertionToGenerate.NON_NULL:
                return AssertionResult(
                    [],
                    [
                        ast.Assert(
                            test=ast.Compare(
                                left=ast.Name(id="return_value", ctx=ast.Load()),
                                ops=[ast.IsNot()],
                                comparators=[ast.Constant(value=None)],
                            )
                        )
                    ],
                )
            case AssertionToGenerate.TYPE:
                return AssertionResult(
                    [],
                    [
                        ast.Assert(
                            test=ast.Compare(
                                left=ast.Attribute(value=ast.Call(func=ast.Name(id="type", ctx=ast.Load()),
                                              args=[ast.Name(id="return_value", ctx=ast.Load())]),
                                                   attr='__name__', ctx=ast.Load()),
                                ops=[ast.Eq()],
                                comparators=[ast.Constant(value=self.type_data)],
                            ),
                        )
                    ],
                )
            case AssertionToGenerate.LENGTH:
                return AssertionResult(
                    [],
                    [
                        ast.Assert(
                            test=ast.Compare(
                                left=ast.Call(
                                    func=ast.Name(id="len", ctx=ast.Load()),
                                    args=[ast.Name(id="return_value", ctx=ast.Load())],
                                ),
                                ops=[ast.Eq()],
                                comparators=[ast.Constant(value=len(value))],
                            )
                        )
                    ],
                )
            case AssertionToGenerate.REPR:
                return AssertionResult(
                    [],
                    [
                        ast.Assert(
                            test=ast.Compare(
                                left=ast.Name(id="return_value", ctx=ast.Load()),
                                ops=[ast.Eq()],
                                comparators=[ast.Constant(value=repr(value))],
                            )
                        )
                    ],
                )
            case AssertionToGenerate.PICKLE:
                arr_reconstructor = PickleReconstructor(fut_path)
                if fixture := arr_reconstructor.make_fixture(
                    "saved_return_value", value
                ):
                    return AssertionResult(
                        [fixture],
                        [
                            ast.Assert(
                                test=ast.Compare(
                                    left=ast.Name(id="return_value", ctx=ast.Load()),
                                    ops=[ast.Eq()],
                                    comparators=[  # FIXME: go to meta_fixture and have these be automatically generated
                                        ast.Name(
                                            id="saved_return_value", ctx=ast.Load()
                                        )
                                    ],
                                ),
                                msg=None,
                            )
                        ],
                    )

                return AssertionResult([], [])
            case AssertionToGenerate.ARR:
                arr_reconstructor = ArgumentReconstructor(fut_path)
                if fixture := arr_reconstructor.make_fixture(
                    "saved_return_value", value
                ):
                    return AssertionResult(
                        [fixture],
                        [
                            ast.Assert(
                                test=ast.Compare(
                                    left=ast.Name(id="return_value", ctx=ast.Load()),
                                    ops=[ast.Eq()],
                                    comparators=[  # FIXME: go to meta_fixture and have these be automatically generated
                                        ast.Name(
                                            id="saved_return_value", ctx=ast.Load()
                                        )
                                    ],
                                ),
                                msg=None,
                            )
                        ],
                    )

                return AssertionResult([], [])
            case AssertionToGenerate.NONE:
                return AssertionResult([], [])
            case _:
                assert False
