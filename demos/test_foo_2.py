import dill
import pytest
import linkedlist


@pytest.fixture
def generate_list_of_obj():
    list_of_obj = ["a"]
    return list_of_obj


@pytest.fixture
def generate_x():
    with open(
        "/Users/randyzhu/Desktop/2025S-Explotest/explotest/demos/pickled/x_1eb77c47.pkl",
        "rb",
    ) as f:
        x = dill.loads(f.read())
    return x


def test_foo(generate_x):
    x = generate_x
    return_value = linkedlist.foo(x)
