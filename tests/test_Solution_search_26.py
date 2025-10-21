import dill
import pytest

import demos.leetcode_417 as leetcode_417


@pytest.fixture(autouse=True)
def mock_setup():
    import os

    os.environ["RUNNING_GENERATED_TEST"] = "true"


@pytest.fixture
def generate_self():
    with open(
        "pickled/self_e886d1b7.pkl", "rb"
    ) as f:
        self = dill.loads(f.read())
    return self


@pytest.fixture
def generate_y():
    y = 0
    return y


@pytest.fixture
def generate_x():
    x = 0
    return x


@pytest.fixture
def generate_heights():
    heights = [[1]]
    return heights


def test_Solution_search(generate_self, generate_y, generate_x, generate_heights):
    self = generate_self
    y = generate_y
    x = generate_x
    heights = generate_heights
    return_value = leetcode_417.Solution.search(self, y, x, heights)
