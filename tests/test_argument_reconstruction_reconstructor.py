import ast
import re

from pytest import fixture

from src.explotest.argument_reconstruction_reconstructor import (
    ArgumentReconstructionReconstructor,
)


@fixture
def setup(tmp_path):
    arr = ArgumentReconstructionReconstructor(tmp_path)
    d = tmp_path / "pickled"
    d.mkdir()
    yield arr


def test_reconstruct_object_instance(setup):
    class Foo:
        x = 1
        y = 2

    asts = setup.asts({"x": Foo()})
    assert len(asts) == 1
    ptf = asts[0]
    assert ptf.depends == []
    assert ptf.parameter == "x"
    assert len(ptf.body) == 3
    assign = ptf.body[0]
    expr_1 = ptf.body[1]
    expr_2 = ptf.body[2]

    assert ast.unparse(assign) == "clone_x = Foo.__new__(Foo)"
    assert ast.unparse(expr_1) == "setattr(clone_x, 'x', 1)"
    assert ast.unparse(expr_2) == "setattr(clone_x, 'y', 2)"


def test_reconstruct_object_instance_recursive_1(setup):

    class Bar:
        pass

    class Foo:
        bar = Bar()

    """
    f = Foo()
    setup.asts({"x": f})
    
    x = Foo.__new__(Foo)
    
    bar = Bar.__new__(Bar)
    setattr(x, "bar", bar)
    # TODO: add quotes here
    """

    x = Foo.__new__(Foo)

    bar = Bar.__new__(Bar)
    setattr(x, bar, bar)


def test_reconstruct_object_instance_recursive_2(setup):
    class Baz:
        pass

    class Bar:
        baz = Baz()

    class Foo:
        bar = Bar()

    f = Foo()
    ArgumentReconstructionReconstructor._reconstruct_object_instance(f)


def test_reconstruct_lambda(setup):
    # should be the same as pickling
    asts = setup.asts({"f": lambda x: x + 1})

    assert len(asts) == 1
    assert asts[0].depends == []
    assert asts[0].parameter == "f"
    pattern = r"with open\(..*\) as f:\s+f = dill\.loads\(f\.read\(\)\)"
    assert re.search(pattern, ast.unparse(asts[0].body[0]))
