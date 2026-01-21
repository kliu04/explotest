import ast

import pytest

from explotest.autoassert.autoassert import AssertionGenerator, AssertionToGenerate
from explotest.autoassert.test_runner import ExecutionResult


@pytest.fixture
def ag_type():
    ag = AssertionGenerator()
    ag.assertion_to_generate = AssertionToGenerate.TYPE
    ag.type_data = "list"
    return ag


@pytest.fixture
def ag_null():
    ag = AssertionGenerator()
    ag.assertion_to_generate = AssertionToGenerate.NULL
    return ag


def test_type(ag_type):
    # fut_path does not matter
    assertions = ag_type.generate_assertion(value=[], fut_path="").assertions
    # print([ast.unparse(a) for a in assertion.assertions])
    assert len(assertions) == 1
    assert ast.unparse(assertions[0]) == "assert type(return_value).__name__ == 'list'"


def test_null(ag_null):
    assertions = ag_null.generate_assertion(value=[], fut_path="").assertions
    assert len(assertions) == 1
    assert ast.unparse(assertions[0]) == "assert return_value is None"
