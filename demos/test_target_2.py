import dill
import pytest
import iomockdemo


@pytest.fixture(autouse=True)
def mock_setup():
    import os

    os.environ["RUNNING_GENERATED_TEST"] = "true"


def test_target():
    return_value = iomockdemo.target()
