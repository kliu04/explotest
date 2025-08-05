import inspect
import os
from ast import parse

import openai
import pytest
import requests
from dotenv import load_dotenv

from explotest.event_analyzer_for_global_state import EventAnalyzer
from explotest.global_state_detector import find_global_vars, find_function_def
from explotest.test_generator import TestGenerator

load_dotenv()

GEMINI_CONNECTION = openai.OpenAI(
    base_url=r"https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv("GEMINI_KEY"),
)


# Our FUT
def get_weather_data(city: str) -> dict:
    """Fetches weather data from the Open-Meteo API."""
    # Step 1: Get coordinates for the city using the Open-Meteo Geocoding API
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search"
    geo_params = {"name": city, "count": 1}
    print(f"NETWORK: Getting coordinates for {city}...")
    try:
        geo_res = requests.get(geo_url, params=geo_params, timeout=10)
        geo_res.raise_for_status()
        geo_data = geo_res.json()
        if not geo_data.get("results"):
            return {"error": f"Could not find coordinates for city: {city}"}

        location = geo_data["results"][0]
        lat, lon = location["latitude"], location["longitude"]
        print(f"NETWORK: Found coordinates: Lat={lat}, Lon={lon}")

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to geocoding service: {e}"}

    # Step 2: Get the weather for the coordinates
    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params = {"latitude": lat, "longitude": lon, "current_weather": "true"}
    print(f"NETWORK: Getting weather for {city}...")
    try:
        weather_res = requests.get(weather_url, params=weather_params, timeout=10)
        weather_res.raise_for_status()
        return weather_res.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to weather service: {e}"}


@pytest.fixture
def analyzer() -> EventAnalyzer:
    return EventAnalyzer(
        proc_filter=(
            get_weather_data.__name__,
            inspect.getsourcefile(get_weather_data),
        ),
        capture_names_in_proc=find_global_vars(
            source=parse(inspect.getsource(get_weather_data)),
            proc_name=get_weather_data.__name__,
        ),
        fn_def=find_function_def(
            parse(inspect.getsource(get_weather_data), get_weather_data.__name__)
        ),
        llm=GEMINI_CONNECTION,
        model="gemini-2.5-flash-lite",
    )


@pytest.fixture
def analysis_result(analyzer: EventAnalyzer) -> dict[str, object]:
    analyzer.start_tracking()
    get_weather_data("Vancouver")
    tracking_result = analyzer.end_tracking()
    assert tracking_result is not None
    assert "requests" in tracking_result.keys()
    return tracking_result


def test_create_test_and_mock_setup_for_get_weather_data(analysis_result):
    mocks = TestGenerator.create_mocks(list(analysis_result.keys()))
    assert len(mocks) == 1
