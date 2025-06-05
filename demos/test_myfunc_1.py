import dill
import pytest
import nameclash


@pytest.fixture
def generate_foo():
    clone_foo = nameclash.Foo.__new__(nameclash.Foo)
    setattr(clone_foo, "x", 1)
    setattr(clone_foo, "y", 2)
    return clone_foo


@pytest.fixture
def generate_bar():
    clone_bar = nameclash.Bar.__new__(nameclash.Bar)
    setattr(clone_bar, "x", 3)
    setattr(clone_bar, "y", 4)
    return clone_bar


@pytest.fixture
def generate_bar2():
    clone_bar2 = nameclash.Bar.__new__(nameclash.Bar)
    setattr(clone_bar2, "x", 3)
    setattr(clone_bar2, "y", 4)
    return clone_bar2


def test_myfunc(generate_foo, generate_bar, generate_bar2):
    foo = generate_foo
    bar = generate_bar
    bar2 = generate_bar2
    return_value = nameclash.myfunc(foo, bar, bar2)
