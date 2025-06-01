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

    asts = setup.asts({"f": Foo()})
    assert len(asts) == 1

    ptf = asts[0]

    assert len(ptf.depends) == 1
    dependency = ptf.depends[0]
    assert dependency.parameter == "bar"
    assert len(dependency.body) == 1
    assert ast.unparse(dependency.body[0]) == "clone_bar = Bar.__new__(Bar)"
    assert ast.unparse(dependency.ret) == "return clone_bar"

    assert ptf.parameter == "f"
    assert ast.unparse(ptf.body[0]) == "clone_f = Foo.__new__(Foo)"
    assert ast.unparse(ptf.body[1]) == "setattr(clone_f, 'bar', generate_bar)"


def test_reconstruct_object_instance_recursive_2(setup):
    class Baz:
        pass

    class Bar:
        baz = Baz()

    class Foo:
        bar = Bar()

    f = Foo()
    asts = setup.asts({"f": f})
    assert len(asts) == 1

    ptf = asts[0]

    # bar
    assert len(ptf.depends) == 1
    dependency_bar = ptf.depends[0]
    assert dependency_bar.parameter == "bar"
    assert len(dependency_bar.body) == 2
    assert ast.unparse(dependency_bar.body[0]) == "clone_bar = Bar.__new__(Bar)"
    assert (
        ast.unparse(dependency_bar.body[1]) == "setattr(clone_bar, 'baz', generate_baz)"
    )
    assert ast.unparse(dependency_bar.ret) == "return clone_bar"

    # baz
    assert len(dependency_bar.depends) == 1
    dependency_baz = dependency_bar.depends[0]
    assert dependency_baz.parameter == "baz"
    assert len(dependency_baz.body) == 1
    assert ast.unparse(dependency_baz.body[0]) == "clone_baz = Baz.__new__(Baz)"
    assert ast.unparse(dependency_baz.ret) == "return clone_baz"

    assert ptf.parameter == "f"
    assert ast.unparse(ptf.body[0]) == "clone_f = Foo.__new__(Foo)"
    assert ast.unparse(ptf.body[1]) == "setattr(clone_f, 'bar', generate_bar)"
    print(ast.unparse(ptf.body[0]))
    print(ast.unparse(ptf.body[1]))


def test_reconstruct_lambda(setup):
    # should be the same as pickling
    asts = setup.asts({"f": lambda x: x + 1})

    assert len(asts) == 1
    assert asts[0].depends == []
    assert asts[0].parameter == "f"
    pattern = r"with open\(..*\) as f:\s+f = dill\.loads\(f\.read\(\)\)"
    assert re.search(pattern, ast.unparse(asts[0].body[0]))
