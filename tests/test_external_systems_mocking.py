import ast
import inspect
import os
from typing import Callable, Any

import openai
import pytest
from dotenv import load_dotenv

import test_data.test_event_analyzer.external_systems as test_fns
from explotest.event_analyzer_for_global_state import EventAnalyzer
from explotest.global_state_detector import find_global_vars

load_dotenv()

GEMINI_CONNECTION = openai.OpenAI(
    base_url=r"https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv("GEMINI_KEY"),
)

OLLAMA_CONNECTION = openai.OpenAI(
    base_url="http://localhost:11434/v1", api_key="ollama"
)

FUTS: list[tuple[str, Callable[[Any], Any]]] = list(
    filter(
        lambda t: t[0][0] != "_" and callable(t[1]) and t[0] != "run_examples",
        inspect.getmembers(test_fns),
    )
)
FUT_NAMES = list(map(lambda fut: fut[0], FUTS))

expected_results = {
    "add_item_to_cache": ["_in_memory_cache"],
    "get_item_from_cache": [],
    "clear_cache": ["_in_memory_cache"],
    "connect_to_database": ["psycopg"],
    "setup_database": [],
    "get_user_from_db": [],
    "get_weather_data": ["requests"],
}


@pytest.mark.parametrize(
    "oai,model",
    [
        (
            GEMINI_CONNECTION,
            "gemini-2.5-flash-lite",
        ),
        (
            GEMINI_CONNECTION,
            "gemini-2.5-pro",
        ),
        (
            GEMINI_CONNECTION,
            "gemini-2.5-flash",
        ),
        (OLLAMA_CONNECTION, "gemma3n:e2b"),
        (OLLAMA_CONNECTION, "gemma3n:e4b"),
        (OLLAMA_CONNECTION, "qwen2.5-coder:0.5b"),
        (OLLAMA_CONNECTION, "deepseek-coder"),
        # (OLLAMA_CONNECTION, "deepseek-r1:8b"),
    ],
    ids=[
        "gemini-flash-lite",
        "gemini-flash",
        "gemini-pro",
        "ollama-gemma-e2b",
        "ollama-gemma-e4b",
        "ollama-qwen2.5-coder-0.5b",
        "ollama-deepseek-coder",
        # "ollama-deepseek-r1-8b",
    ],
)
@pytest.mark.parametrize("fut", FUTS, ids=FUT_NAMES)
class gTestExternalSystemsMocking:
    @pytest.fixture
    def fut_src(self, fut) -> ast.Module:
        fut_src = ast.parse(inspect.getsource(fut[1]))
        return fut_src

    @pytest.fixture
    def global_candidates(self, fut_src, fut) -> list[str]:
        globals_found = [str(ext) for ext in find_global_vars(fut_src, fut[0])]
        return globals_found

    @pytest.fixture
    def analyzer(
        self,
        fut: tuple[str, Callable],
        oai: openai.OpenAI,
        global_candidates,
        fut_src,
        model: str,
    ) -> EventAnalyzer:

        target_function = (fut[0], inspect.getfile(fut[1]))
        print(f"Target Function is at: {target_function}")
        return EventAnalyzer(target_function, global_candidates, fut_src, oai, model)

    def test_fut(self, analyzer, fut, global_candidates):
        print(f"Running test for {fut[0]}")
        print(f"Candidate globals: {global_candidates}")
        analyzer.start_tracking()
        test_fns.run_examples()
        res = analyzer.end_tracking()
        print(f"Globals to mock: {res}")
        assert set(expected_results[fut[0]]) == set(res.keys())
