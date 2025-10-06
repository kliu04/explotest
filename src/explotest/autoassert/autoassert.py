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


class AssertionToGenerate(Enum):
    NON_EXISTENCE = -1
    NONE = 0
    EXISTENCE = 1
    LENGTH = 2
    TOTAL_EQUALITY_REPR = 3
    TOTAL_EQUALITY_PICKLE = 4
    TOTAL_EQUALITY_ARR = 5


@dataclass
class AssertionResult:
    fixtures: list[MetaFixture]
    assertions: list[ast.Assert]


def determine_assertion(er: ExecutionResult) -> AssertionToGenerate:
    """ """

    if er.result_from_run_one == er.result_from_run_two:
        if ArgumentReconstructor.is_reconstructible(er.result_from_run_one):
            return AssertionToGenerate.TOTAL_EQUALITY_REPR
        else:
            try:
                dill.dumps(er.result_from_run_one)  # try to serialize...
                # success if we reach this block
                return AssertionToGenerate.TOTAL_EQUALITY_PICKLE
            except Exception:
                # not pickleable, not ARR-able, try to use __repr__
                return AssertionToGenerate.TOTAL_EQUALITY_REPR
    else:
        # okay, they aren't equal by any notion
        # are they at least the same type?
        if type(er.result_from_run_one) is not type(er.result_from_run_two):
            # if they're both null, at least we can check for non-existence
            if er.result_from_run_one is None and er.result_from_run_two is None:
                return AssertionToGenerate.NON_EXISTENCE
            else:
                # this means they have different types, which also captures the case where one object is none and the
                # other is not none. there's no meaningful assertion to generate between two objects of *different* types.
                return AssertionToGenerate.NONE  # :(
        else:
            # if they're the same type, let's see if it has a __len__ quality
            if getattr(er.result_from_run_one, "__len__", False):
                if len(er.result_from_run_one) == len(
                    er.result_from_run_two
                ):  # if the lengths are equal, let's use length
                    return AssertionToGenerate.LENGTH
                else:
                    return AssertionToGenerate.TOTAL_EQUALITY_REPR
            else:
                return AssertionToGenerate.NONE


def generate_assertion(
    value: Any, kind: AssertionToGenerate, value_name: str = "return_value"
) -> AssertionResult:
    match kind:
        case AssertionToGenerate.NON_EXISTENCE:
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

        case AssertionToGenerate.NONE:
            return AssertionResult([], [])
        case AssertionToGenerate.EXISTENCE:
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
        case AssertionToGenerate.TOTAL_EQUALITY_REPR:
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

        case AssertionToGenerate.TOTAL_EQUALITY_PICKLE:
            return AssertionResult([], [])  # todo: implement
        case AssertionToGenerate.TOTAL_EQUALITY_ARR:
            return AssertionResult([], [])
        case _:
            assert False
