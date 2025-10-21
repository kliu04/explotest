import dill
import pytest

import demos.environment as environment


@pytest.fixture(autouse=True)
def mock_setup():
    import os

    os.environ["RUNNING_GENERATED_TEST"] = "true"


@pytest.fixture
def generate_env():
    with open(
        "pickled/env_73a59df3.pkl", "rb"
    ) as f:
        env = dill.loads(f.read())
    return env


@pytest.fixture
def generate_x():
    x = "y"
    return x


def test_lookup_env(generate_env, generate_x):
    env = generate_env
    x = generate_x
    return_value = environment.lookup_env(env, x)
