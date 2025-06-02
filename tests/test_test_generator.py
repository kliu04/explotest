import ast
from pathlib import Path

from pytest import fixture

from src.explotest.helpers import Mode
from src.explotest.test_generator import TestGenerator


@fixture
def pickle_setup(tmp_path: Path):
    return TestGenerator("foo", tmp_path, Mode.PICKLE)


def test_generate(pickle_setup):
    generated_test = pickle_setup.generate({"x": 1})
    assert len(generated_test.imports) == 3
    assert generated_test.imports[0].names[0].name == "dill"
    assert generated_test.imports[1].names[0].name == "pytest"
    assert (generated_test.imports[2].names[0].name == "test_generate0")  # name depends on pytest implementation detail
    assert (ast.unparse(generated_test.act_phase) == "return_value = test_generate0.foo(x)")
