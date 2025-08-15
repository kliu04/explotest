from ast import *

import pytest

from src.explotest.generated_test import GeneratedTest
from src.explotest.pytest_fixture import PyTestFixture
from .test_fixture_generation import sample_arg_reconstruct_body


class TestGeneratedTest:
    fixture_afpbs = PyTestFixture(
        [],
        "abstract_factory_proxy_bean_singleton",
        [Pass()],
        Return(value=Constant(value=None)),
    )
    fixture_kevin_liu = PyTestFixture(
        [], "kevin_liu", [Pass()], Return(value=Constant(value=None))
    )
    fixture_x = PyTestFixture(
        [fixture_afpbs, fixture_kevin_liu],
        "x",
        sample_arg_reconstruct_body(),
        Return(value=Constant(value=None)),
    )
    assignment = Assign(
        targets=[Name(id="result", ctx=Store())],
        value=Call(func=Name(id="call", ctx=Load()), args=[Name(id="x")]),
    )
    imports = [
        parse("import math").body[0],
        parse("import numpy as np").body[0],
        parse("from math import sqrt").body[0],
        parse("from math import sqrt, ceil").body[0],
        parse("from math import *").body[0],
        parse("import os.path as osp").body[0],
        parse("from . import expected_test").body[0],
    ]
    all_imports = [fixture_kevin_liu, fixture_afpbs, fixture_x]

    @pytest.fixture
    def tut(self):
        tut = GeneratedTest(
            "call", self.imports, self.all_imports, self.assignment, [], []
        )
        return tut

    @pytest.mark.skip(reason="Too flaky")
    def test_whole_test_generation(self, tut):
        from pathlib import Path

        test_read = Path(
            "../test_data/test_generated_test_expected_test.py"
        ).read_text()
        compiled = parse(test_read)
        assert unparse(compiled) == unparse(tut.ast_node)


class TestActFunctionGeneration(TestGeneratedTest):
    def test_act_function_fixture_requests_are_minimal(self, tut):
        test_function_args = tut.act_function_def_ast.args
        assert (
            len(test_function_args.args) == 1
        )  # should only request x fixture & x depennds on afps and kevin_liu.
        assert test_function_args.args[0].arg == "generate_x"

    def test_act_function_has_assignment_body(self, tut):
        test_function_body = tut.act_function_def_ast.body
        assert unparse(self.assignment) in [
            unparse(node) for node in test_function_body
        ]

    def test_act_function_test_name_is_valid(self, tut):
        act_function = tut.act_function_def_ast
        assert act_function.name == "test_call"

    # def test_act_function_with_kwargs(self, tut):
