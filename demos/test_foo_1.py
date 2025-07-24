import dill
import pytest
import linkedlist

@pytest.fixture
def generate_x():
    with open('/Users/randyzhu/Desktop/2025S-Explotest/explotest/demos/pickled/x_ed4bbc99.pkl', 'rb') as f:
        x = dill.loads(f.read())
    return x

def test_foo(generate_x):
    x = generate_x
    return_value = linkedlist.foo(x)