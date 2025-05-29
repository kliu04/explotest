from ast import *

import pytest

from src.explotest.generated_test import GeneratedTest
from src.explotest.pytest_fixture import PyTestFixture
from test_fixture_generation import sample_arg_reconstruct_body


class TestGeneratedTest:
    fixture_afpbs = PyTestFixture([], 'abstract_factory_proxy_bean_singleton',
                                  [Pass()])
    fixture_kevin_liu = PyTestFixture([], 'kevin_liu', [Pass()])
    fixture_x = PyTestFixture([fixture_afpbs, fixture_kevin_liu], 'x',
                              sample_arg_reconstruct_body())

    @pytest.fixture
    def tut(self):
        tut = GeneratedTest(
            [parse('import math').body[0], parse('import numpy as np').body[0], parse('from math import sqrt').body[0],
             parse('from math import sqrt, ceil').body[0], parse('from math import *').body[0],
             parse('import os.path as osp').body[0],
             parse('from . import sibling_module\nfrom ..subpackage import module').body[0]],
            [self.fixture_kevin_liu, self.fixture_afpbs, self.fixture_x],
            Assign(targets=[Name(id='result', ctx=Store())],
                   value=Call(func=Name(id='call', ctx=Load()))),
            [], []
        )
        return tut

    def test_function_definition_imports_are_minimal(self, tut):
        test_function_args = tut.act_function_def.args
        assert len(test_function_args.args) == 1 # should only request x fixture & x depennds on afps and kevin_liu.
        assert test_function_args.args[0].arg == 'x'

    def test_act_function_has_assignment_body(self, tut):