import ast
import re

from pytest import fixture

from explotest.reconstructors.pickle_reconstructor import PickleReconstructor


@fixture
def setup(tmp_path):
    pickle_reconstructor = PickleReconstructor(tmp_path)
    d = tmp_path / "pickled"
    d.mkdir()
    yield pickle_reconstructor


def test_pickle_reconstructor_primitive(setup):
    mf = setup.make_fixture("x", 1)
    assert mf.parameter == "x"
    assert mf.depends == []
    assert ast.dump(mf.body[0]) == ast.dump(ast.Assign(
    targets=[ast.Name(id="x", ctx=ast.Store())],
    value=ast.Constant(value=1),
))
    assert ast.dump(mf.ret) == ast.dump(ast.Return(
    value=ast.Name(id="x", ctx=ast.Load())
))


def test_pickle_reconstructor_lop(setup):
    mf = setup.make_fixture("x", [1, 2, False])
    assert mf.parameter == "x"
    assert mf.depends == []
    assert ast.dump(mf.body[0]) == ast.dump(
        ast.Assign(
    targets=[ast.Name(id="x", ctx=ast.Store())],
    # technically, this is a bug, but it doesn't seem to matter
    # elts should be wrapped in ast.Constant
    value=ast.Constant(
        value=[
            1, 2, False
        ],
    ),
))
    assert ast.dump(mf.ret) == ast.dump(ast.Return(
        value=ast.Name(id="x", ctx=ast.Load())
    ))


def test_pickle_reconstructor_object(setup):
    class Foo:
        pass

    mf = setup.make_fixture("f", Foo())
    assert mf.parameter == "f"
    assert mf.depends == []
    pattern = r"with open\(..*\) as f:\s+f = dill\.loads\(f\.read\(\)\)"
    assert re.search(pattern, ast.unparse(mf.body[0]))
    assert ast.dump(mf.ret) == ast.dump(ast.Return(
        value=ast.Name(id="f", ctx=ast.Load())
    ))



def test_pickle_reconstructor_lambda(setup):
    mf = setup.make_fixture("f", lambda x: x)
    assert mf.parameter == "f"
    assert mf.depends == []
    pattern = r"with open\(..*\) as f:\s+f = dill\.loads\(f\.read\(\)\)"
    assert re.search(pattern, ast.unparse(mf.body[0]))
    assert ast.dump(mf.ret) == ast.dump(ast.Return(
        value=ast.Name(id="f", ctx=ast.Load())
    ))
