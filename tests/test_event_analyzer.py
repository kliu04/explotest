from typing import Any, Generator

import pytest

from explotest.event_analyzer_for_global_state import EventAnalyzer


@pytest.fixture
def analyzer():
    eva = EventAnalyzer()
    eva.start_tracking()
    return eva


def test_one(analyzer):
    print("test")
    print("meow")
    assert True
    analyzer.end_tracking()
