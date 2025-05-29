import pytest
import math
import numpy as np
from math import sqrt
from math import sqrt, ceil
from math import *
import os.path as osp
from . import expected_test

@pytest.fixture
def generate_kevin_liu():
    pass

@pytest.fixture
def generate_abstract_factory_proxy_bean_singleton():
    pass


@pytest.fixture
def generate_x(generate_abstract_factory_proxy_bean_singleton, generate_kevin_liu):
    x = Foo()
    x.y = 'Meow!'
    return x

def test_call(generate_x):
    x = generate_x
    result = call(x)