from typing import Any, Generator

import pytest
import ast

from explotest.event_analyzer_for_global_state import EventAnalyzer


@pytest.fixture
def analyzer():
    eva = EventAnalyzer("foo", [ast.Name(id="L", ctx=ast.Load())])
    eva.start_tracking()
    return eva


L = []


def foo():
    L.append("meow")
    return 1


def test_one(analyzer):
    print("test")
    print("meow")
    assert True
    foo()
    print(analyzer.end_tracking())
