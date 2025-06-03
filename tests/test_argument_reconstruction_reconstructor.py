import abc
import ast
import re
from abc import abstractmethod

import pytest
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
    assert ptf.parameter == "x"
    assert len(ptf.body) == 3
    assign = ptf.body[0]
    expr_1 = ptf.body[1]
    expr_2 = ptf.body[2]

    assert (
        ast.unparse(assign)
        == "clone_x = test_argument_reconstruction_reconstructor.Foo.__new__(test_argument_reconstruction_reconstructor.Foo)"
    )
    assert ast.unparse(expr_1) == "setattr(clone_x, 'x', 1)"
    assert ast.unparse(expr_2) == "setattr(clone_x, 'y', 2)"


def test_reconstruct_object_instance_recursive_1(setup):

    class Bar:
        pass

    class Foo:
        bar = Bar()

    asts = setup.asts({"f": Foo()})
    assert len(asts) == 2

    ptf = asts[0]

    assert len(ptf.depends) == 1
    dependency = ptf.depends[0]
    assert re.search("bar_.*", ptf.depends[0].parameter )
    assert len(dependency.body) == 1
    re.search(
       "clone_bar_.* = .*\.Bar\.__new__(.*\.Bar)",
        ast.unparse(dependency.body[0]))
    assert re.search("return clone_bar_.*", ast.unparse(dependency.ret))

    assert ptf.parameter == "f"
    assert (
        ast.unparse(ptf.body[0])
        == "clone_f = test_argument_reconstruction_reconstructor.Foo.__new__(test_argument_reconstruction_reconstructor.Foo)"
    )
    assert re.match("setattr\(clone_f, 'bar', generate_bar_.*\)", ast.unparse(ptf.body[1]))


def test_reconstruct_object_instance_recursive_2(setup):
    class Baz:
        pass

    class Bar:
        baz = Baz()

    class Foo:
        bar = Bar()

    f = Foo()
    asts = setup.asts({"f": f})
    assert len(asts) == 3

    ptf = asts[0]

    # bar
    assert len(ptf.depends) == 1
    dependency_bar = ptf.depends[0]
    assert len(dependency_bar.body) == 2
    assert re.search(
        "clone_bar_.* = .*\.Bar\.__new__(.*\.Bar)",
        ast.unparse(dependency_bar.body[0])
    )
    assert re.search(
        "setattr\(clone_bar_.*, 'baz', generate_baz_.*\)",
        ast.unparse(dependency_bar.body[1])
    )
    assert re.search("return clone_bar_.*", ast.unparse(dependency_bar.ret))

    # baz
    assert len(dependency_bar.depends) == 1
    dependency_baz = dependency_bar.depends[0]
    assert len(dependency_baz.body) == 1
    assert re.search(
        "clone_baz_.* = .*\.Baz\.__new__(.*\.Baz)",
        ast.unparse(dependency_baz.body[0])
    )
    assert re.search("return clone_baz_.*", ast.unparse(dependency_baz.ret))

    assert ptf.parameter == "f"
    assert (
        ast.unparse(ptf.body[0])
        == "clone_f = test_argument_reconstruction_reconstructor.Foo.__new__(test_argument_reconstruction_reconstructor.Foo)"
    )
    assert re.search("setattr\(clone_f, 'bar', generate_bar_.*\)", ast.unparse(ptf.body[1]))
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


def test_reconstruct_list(setup):
    class Foo:
        pass

    asts = setup.asts({"f": [1, Foo(), Foo()]})

    assert len(asts) == 3
    assert len(asts[0].depends) == 2
    assert asts[0].depends[0] is asts[1]
    assert asts[0].depends[1] is asts[2]

    pattern = r"clone_Foo_.+ = .+.Foo.__new__(.*.Foo)"
    print(ast.unparse(asts[1].body[0]))
    assert re.search(pattern, ast.unparse(asts[1].body[0]))
    assert re.search(pattern, ast.unparse(asts[2].body[0]))

    pattern = r"f = \[1, generate_Foo_.+, generate_Foo_.+\]"
    print(ast.unparse(asts[0].body[0]))
    assert re.search(pattern, ast.unparse(asts[0].body[0]))


is_class_instance = ArgumentReconstructionReconstructor.is_class_instance


class TestObjectDetection:
    def test_generator(self):
        def generator_creator(n: int):
            for i in range(n):
                yield i

        generator = generator_creator(10)
        assert not is_class_instance(generator)

    def test_method(self):
        class C:
            def foo(self):
                return self

        assert not is_class_instance(C.foo)

    def test_func(self):
        def f():
            return

        assert not is_class_instance(f)

    def test_lambda(self):
        assert not is_class_instance(lambda x: x)

    def test_abc(self):
        a = abc.ABC()
        assert is_class_instance(a)
        pytest.fail(reason="decide whether ABC is an instance of a class?")

    def test_abc_inheritor(self):
        class I(abc.ABC):
            pass

        assert is_class_instance(I())

    def test_class(self):
        class A:
            pass

        assert not is_class_instance(A)

    def test_async_fun(self):
        async def coroutine():
            return None

        assert not is_class_instance(coroutine)

    def test_module(self):
        import numpy

        assert not is_class_instance(numpy)

    def test_messed_up_async_generator(self):
        async def generator_async():
            yield None

        assert not is_class_instance(generator_async)

    def test_none(self):
        assert not is_class_instance(None)
