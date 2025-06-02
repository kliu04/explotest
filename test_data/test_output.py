import dill
import pytest
import 

@pytest.fixture
def generate_f():
    with open('./pickled/f_5946fb37.pkl', 'rb') as f:
        f = dill.loads(f.read())
    return f

@pytest.fixture
def generate_x():
    with open('./pickled/x_c8f470c2.pkl', 'rb') as f:
        x = dill.loads(f.read())
    return x

@pytest.fixture
def generate_dx():
    dx = 0.02454369260617026
    return dx

@pytest.fixture
def generate_R():
    R = 1
    return R

def test_tr_rule(generate_f, generate_x, generate_dx, generate_R):
    f = generate_f
    x = generate_x
    dx = generate_dx
    R = generate_R
    return_value = .tr_rule(f, x, dx, R)