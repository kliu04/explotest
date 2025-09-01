import ast
import os

import numpy as np
import openai
import pytest
from dotenv import load_dotenv

from explotest.event_analyzer import EventAnalyzer


@pytest.fixture
def oai() -> openai.OpenAI:
    load_dotenv()
    return openai.OpenAI(
        base_url=r"https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=os.getenv("GEMINI_KEY"),
    )


@pytest.fixture
def analyzer(oai: openai.OpenAI):
    eva = EventAnalyzer(
        ("foo", __file__),
        ["L", "np"],
        ast.parse(
            """
def foo():
    np.sin(30)
    L.append("meow")
    return 1
        """
        ).body[0],
        oai,
    )
    eva.start_tracking()
    return eva


L = []


def foo():
    np.sin(30)
    L.append("meow")
    return 1


def test_one(analyzer):
    foo()
    result = analyzer.end_tracking()
    assert 1 == len(result)
    assert "L" in result
