import dill
import pytest
import nameclash

@pytest.fixture
def generate_foo(generate_x, generate_y):
    clone_foo = nameclash.Foo.__new__(nameclash.Foo)
    setattr(clone_foo, 'x', generate_x)
    setattr(clone_foo, 'y', generate_y)
    return clone_foo

@pytest.fixture
def generate_x():
    x = 1
    return x

@pytest.fixture
def generate_y():
    y = 2
    return y

@pytest.fixture
def generate_bar(generate_x, generate_y):
    clone_bar = nameclash.Bar.__new__(nameclash.Bar)
    setattr(clone_bar, 'x', generate_x)
    setattr(clone_bar, 'y', generate_y)
    return clone_bar

@pytest.fixture
def generate_x():
    x = 3
    return x

@pytest.fixture
def generate_y():
    y = 4
    return y

@pytest.fixture
def generate_bar2(generate_x, generate_y):
    clone_bar2 = nameclash.Bar.__new__(nameclash.Bar)
    setattr(clone_bar2, 'x', generate_x)
    setattr(clone_bar2, 'y', generate_y)
    return clone_bar2

@pytest.fixture
def generate_x():
    x = 3
    return x

@pytest.fixture
def generate_y():
    y = 4
    return y

def test_myfunc(generate_foo, generate_bar, generate_bar2):
    foo = generate_foo
    bar = generate_bar
    bar2 = generate_bar2
    return_value = nameclash.myfunc(foo, bar, bar2)