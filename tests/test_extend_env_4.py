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
        "pickled/env_3f0e5e8a.pkl", "rb"
    ) as f:
        env = dill.loads(f.read())
    return env


@pytest.fixture
def generate_x0():
    x0 = "g"
    return x0


@pytest.fixture
def generate_v():
    v = 40
    return v


def test_extend_env(generate_env, generate_x0, generate_v):
    env = generate_env
    x0 = generate_x0
    v = generate_v
    return_value = environment.extend_env(env, x0, v)
