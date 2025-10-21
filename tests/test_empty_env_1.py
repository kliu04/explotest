import pytest

import demos.environment as environment


@pytest.fixture(autouse=True)
def mock_setup():
    import os

    os.environ["RUNNING_GENERATED_TEST"] = "true"


def test_empty_env():
    return_value = environment.empty_env()
