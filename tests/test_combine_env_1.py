import dill
import pytest

import demos.environment as environment


@pytest.fixture(autouse=True)
def mock_setup():
    import os

    os.environ["RUNNING_GENERATED_TEST"] = "true"


@pytest.fixture
def generate_e0():
    with open(
        "pickled/e0_3d40ff70.pkl", "rb"
    ) as f:
        e0 = dill.loads(f.read())
    return e0


@pytest.fixture
def generate_e1():
    with open(
        "pickled/e1_8f3e141c.pkl", "rb"
    ) as f:
        e1 = dill.loads(f.read())
    return e1


def test_combine_env(generate_e0, generate_e1):
    e0 = generate_e0
    e1 = generate_e1
    return_value = environment.combine_env(e0, e1)
