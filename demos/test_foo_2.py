import dill
import pytest
import meow

@pytest.fixture
def generate_big_bad_global():
    with open('/Users/randyzhu/Desktop/2025S-Explotest/explotest/demos/pickled/big_bad_global_32007ac7.pkl', 'rb') as f:
        big_bad_global = dill.loads(f.read())
    return big_bad_global

@pytest.fixture(autouse=True)
def mock_setup(generate_big_bad_global):
    global big_bad_global

def test_foo():
    return_value = meow.foo()