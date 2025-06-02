import dill
import pytest
from math import sin, pi
import pandas as pd
import numpy as np

def tr_rule(f: pd.Series, x: pd.Series, dx: float, R: int):
    return 2 / pi * dx * (1 / 2 * f.iloc[0] * sin(R * x.iloc[0]) + sum(f.iloc[1:-1] * (x.iloc[1:-1] * R).map(sin)) + 1 / 2 * f.iloc[-1] * sin(R * x.iloc[-1]))

def test_tr_rule(generate_f, generate_x, generate_dx, generate_R):
    f = generate_f
    x = generate_x
    dx = generate_dx
    R = generate_R
    return_value = tr_rule(f, x, dx, R)