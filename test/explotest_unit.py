import pytest

import test_file  # type: ignore


@pytest.fixture
def generate_x():
    return test_file.baz("Hello World!", 7)


@pytest.fixture
def generate_y():
    return 2


def test_foo(generate_x, generate_y):
    x = generate_x
    y = generate_y
    res = test_file.foo(x, y)

    # user inserted
    assert res == 45
