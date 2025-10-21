import dill
import pytest

import demos.vector2 as vector2


@pytest.fixture(autouse=True)
def mock_setup():
    import os

    os.environ["RUNNING_GENERATED_TEST"] = "true"


@pytest.fixture
def generate_self():
    with open(
        "pickled/self_1660d4a2.pkl", "rb"
    ) as f:
        self = dill.loads(f.read())
    return self


@pytest.fixture
def generate_other():
    with open(
        "pickled/other_721787bf.pkl", "rb"
    ) as f:
        other = dill.loads(f.read())
    return other


def test_Vector2___add__(generate_self, generate_other):
    self = generate_self
    other = generate_other
    return_value = vector2.Vector2.__add__(self, other)
