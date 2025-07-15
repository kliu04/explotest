import os
import pathlib

import openai
import pytest
import pytest_mock
from pytest_mock import MockerFixture

import src.explotest.event_analyzer_for_global_state as eva
import src.explotest.global_state_detector as gsd
import ast

import test_data.test_event_analyzer.simpleflask


@pytest.fixture
def oai() -> openai.OpenAI:
    return openai.OpenAI(base_url=r"http://localhost:11434/v1", api_key=r"ollama")


@pytest.fixture
def analyzer(oai: openai.OpenAI) -> eva.EventAnalyzer:
    p = pathlib.Path("../../test_data/test_event_analyzer/simpleflask.py")
    print(os.getcwd())
    sample_file_flask = p.read_text()
    return eva.EventAnalyzer(
        proc_filter=("hello_world", "./test_data/test_event_analyzer/simpleflask.py"),
        capture_names_in_proc=[
            ext.name
            for ext in gsd.find_global_vars(ast.parse(sample_file_flask), "hello_world")
        ],
        oai=oai,
        fn_def=ast.parse(
            """
def hello_world():
    if request.method == "GET":
        return "<p>Hello, World!</p>"
    else:
        return "<p>Goodbye, World!</p>"
        """
        ).body[0],
    )


def test_analyzer(analyzer: eva.EventAnalyzer, mocker: MockerFixture):
    analyzer.start_tracking()
    mock_req = mocker.MagicMock()
    mock_req.method = "POST"
    mocker.patch("test_data.test_event_analyzer.simpleflask.request", new=mock_req)
    test_data.test_event_analyzer.simpleflask.hello_world()
    result = analyzer.end_tracking()
    print(result)
    assert False
