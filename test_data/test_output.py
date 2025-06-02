import dill
import pytest
from math import sin, pi
import pandas as pd
import numpy as np

def tr_rule(f: pd.Series, x: pd.Series, dx: float, R: int):
    return 2 / pi * dx * (1 / 2 * f.iloc[0] * sin(R * x.iloc[0]) + sum(f.iloc[1:-1] * (x.iloc[1:-1] * R).map(sin)) + 1 / 2 * f.iloc[-1] * sin(R * x.iloc[-1]))

@pytest.fixture
def generate_f():
    with open('./pickled/f_050761fb.pkl', 'rb') as f:
        f = dill.loads(f.read())
    return f

@pytest.fixture
def generate_x():
    with open('./pickled/x_092cb9e7.pkl', 'rb') as f:
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
    return_value = tr_rule(f, x, dx, R)