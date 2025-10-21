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
        "pickled/self_3ea88523.pkl", "rb"
    ) as f:
        self = dill.loads(f.read())
    return self


@pytest.fixture
def generate_heights():
    heights = [[1]]
    return heights


def test_Solution_pacificAtlantic(generate_self, generate_heights):
    self = generate_self
    heights = generate_heights
    return_value = leetcode_417.Solution.pacificAtlantic(self, heights)
