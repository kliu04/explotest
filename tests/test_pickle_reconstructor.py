import ast
import re

from pytest import fixture

from src.explotest.pickle_reconstructor import PickleReconstructor


@fixture
def setup(tmp_path):
    pickle_reconstructor = PickleReconstructor(tmp_path)
    d = tmp_path / "pickled"
    d.mkdir()
    yield pickle_reconstructor


def test_pickle_reconstructor_empty(setup):
    asts = setup.asts({})
    assert asts == []


def test_pickle_reconstructor_primitive(setup):
    asts = setup.asts({"x": 1})
    assert len(asts) == 1
    assert asts[0].depends == []
    assert asts[0].parameter == "x"
    assert ast.unparse(asts[0].body[0]) == "x = 1"


def test_pickle_reconstructor_primitives(setup):
    asts = setup.asts({"x": 1, "y": 2, "z": "Hello"})
    assert len(asts) == 3
    assert asts[0].depends == []
    assert asts[0].parameter == "x"
    assert ast.unparse(asts[0].body[0]) == "x = 1"

    assert asts[1].depends == []
    assert asts[1].parameter == "y"
    assert ast.unparse(asts[1].body[0]) == "y = 2"

    assert asts[2].depends == []
    assert asts[2].parameter == "z"
    assert ast.unparse(asts[2].body[0]) == "z = 'Hello'"


def test_pickle_reconstructor_lop(setup):
    asts = setup.asts({"x": [1, 2, False]})
    assert len(asts) == 1
    assert asts[0].depends == []
    assert asts[0].parameter == "x"
    assert ast.unparse(asts[0].body[0]) == "x = [1, 2, False]"


def test_pickle_reconstructor_object(setup):
    class Foo:
        pass

    asts = setup.asts({"f": Foo()})

    assert len(asts) == 1
    assert asts[0].depends == []
    assert asts[0].parameter == "f"
    pattern = r"with open\(.*\) as f:\s+f = dill\.loads\(f\.read\(\)\)"
    assert re.search(pattern, ast.unparse(asts[0].body[0]))
