from typing import Any, Generator

import openai
import pytest
import ast

from explotest.event_analyzer_for_global_state import EventAnalyzer


@pytest.fixture
def oai() -> openai.OpenAI:
    return openai.OpenAI(base_url=r"http://localhost:11434/v1", api_key=r"ollama")


@pytest.fixture
def analyzer(oai: openai.OpenAI):
    eva = EventAnalyzer("foo", [ast.Name(id="L", ctx=ast.Load())], oai)
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
