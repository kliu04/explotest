import abc
import ast
import re

import pandas as pd
import pytest
from pytest import fixture

from explotest.reconstructors.argument_reconstructor import ArgumentReconstructor
from explotest.reconstructors.pickle_reconstructor import PickleReconstructor


@fixture
def setup(tmp_path):
    arr = ArgumentReconstructor(tmp_path, backup_reconstructor=PickleReconstructor)
    d = tmp_path / "pickled"
    d.mkdir()
    yield arr


def test_reconstruct_object_instance(setup):
    class Foo:
        x = 1
        y = 2

    mf = setup.make_fixture("x", Foo())
    assert mf.parameter == "x"
    assert mf.depends == []
    assert len(mf.body) == 3
    pattern = "clone_x = test_.*\.Foo\.__new__()"
    assert re.search(pattern, ast.unparse(mf.body[0]))
    assert ast.unparse(mf.body[1]) == ast.unparse(ast.Expr(
    value=ast.Call(
        func=ast.Name(id="setattr", ctx=ast.Load()),
        args=[
            ast.Name(id="clone_x", ctx=ast.Load()),
            ast.Constant(value="x"),
            ast.Constant(value=1),
        ],
        keywords=[],
    )
))

    assert ast.unparse(mf.body[2]) == ast.unparse(ast.Expr(
        value=ast.Call(
            func=ast.Name(id="setattr", ctx=ast.Load()),
            args=[
                ast.Name(id="clone_x", ctx=ast.Load()),
                ast.Constant(value="y"),
                ast.Constant(value=2),
            ],
            keywords=[],
        )
    ))

    assert ast.dump(mf.ret) == ast.dump(ast.Return(
        value=ast.Name(id="clone_x", ctx=ast.Load())
    ))


def test_reconstruct_object_instance_recursive_1(setup):
    class Bar:
        pass

    class Foo:
        bar = Bar()

    mf = setup.make_fixture("x", Foo())
    assert mf.parameter == "x"
    
    assert len(mf.depends) == 1
    assert mf.depends[0].parameter == "x_bar"
    assert mf.depends[0].depends == []
    assert len(mf.depends[0].body) == 1
    
    
    assert len(mf.body) == 2
    pattern = "clone_x = test_.*\.Foo\.__new__()"
    assert re.search(pattern, ast.unparse(mf.body[0]))
    assert ast.unparse(mf.body[1]) == ast.unparse(ast.Expr(
        value=ast.Call(
            func=ast.Name(id="setattr", ctx=ast.Load()),
            args=[
                ast.Name(id="clone_x", ctx=ast.Load()),
                ast.Constant(value="bar"),
                ast.Name(id="generate_x_bar", ctx=ast.Load()),
            ],
            keywords=[],
        )
    ))


    assert ast.dump(mf.ret) == ast.dump(ast.Return(
        value=ast.Name(id="clone_x", ctx=ast.Load())
    ))

def test_reconstruct_lambda(setup):
    # should be the same as pickling
    mf = setup.make_fixture("f", lambda x: x)

    assert mf.depends == []
    assert mf.parameter == "f"
    pattern = r"with open\(..*\) as f:\s+f = dill\.loads\(f\.read\(\)\)"
    assert re.search(pattern, ast.unparse(mf.body[0]))


def test_reconstruct_list(setup):
    class Foo:
        pass

    mf = setup.make_fixture("f", [1, Foo(), Foo()])
    
    assert len(mf.depends) == 2
    pattern = "Foo_.+"
    assert re.search(pattern, mf.depends[0].parameter)
    pattern = "clone_Foo_.+ = test_.*\.Foo\.__new__()"
    assert re.search(pattern, ast.unparse(mf.depends[0].body[0]))
    
    assert mf.parameter == "f"
    pattern = r"clone_f = \[1, generate_Foo_.+, generate_Foo_.+\]"
    assert re.search(pattern, ast.unparse(mf.body[0]))
    
@pytest.mark.skip()
def test_reconstruct_circular(setup):
    class Foo:
        pass
    class Bar:
        pass
    f = Foo()
    b = Bar()
    f.x = b
    b.x = f

    mf = setup.make_fixture("z", f)

    print(ast.unparse(mf.make_fixture()[0]))
    print(ast.unparse(mf.make_fixture()[1]))


    


is_reconstructible = ArgumentReconstructor.is_reconstructible


class TestObjectDetection:
    def test_generator(self):
        def generator_creator(n: int):
            for i in range(n):
                yield i

        generator = generator_creator(10)
        assert not is_reconstructible(generator)

    def test_method(self):
        class C:
            def foo(self):
                return self

        assert not is_reconstructible(C.foo)

    def test_func(self):
        def f():
            return

        assert not is_reconstructible(f)

    def test_lambda(self):
        assert not is_reconstructible(lambda x: x)

    def test_abc(self):
        a = abc.ABC()
        assert is_reconstructible(a)
        # pytest.fail(reason="decide whether ABC is an instance of a class?")

    def test_abc_inheritor(self):
        class I(abc.ABC):
            pass

        assert is_reconstructible(I())

    def test_class(self):
        class A:
            pass

        assert not is_reconstructible(A)

    def test_async_fun(self):
        async def coroutine():
            return None

        assert not is_reconstructible(coroutine)

    def test_module(self):
        import numpy

        assert not is_reconstructible(numpy)

    def test_messed_up_async_generator(self):
        async def generator_async():
            yield None

        assert not is_reconstructible(generator_async)

    def test_none(self):
        assert is_reconstructible(None)

    def test_vanilla_obj(self):
        class Vanilla:
            def __init__(self, x):
                self.x = x

        v = Vanilla(10)
        assert is_reconstructible(v)

    def test_vanilla_obj_with_evil_topping(self):
        class Vanilla:
            def __init__(self, x):
                self.x = x

        def evil_generator():
            yield 1

        v = Vanilla(evil_generator())
        assert not is_reconstructible(v)

    def test_cycle_detection(self):
        class Node:
            def __init__(self, next):
                self.next = next

        n1 = Node(None)
        n2 = Node(None)

        # couple n1 to n2, n2 to n1
        n1.next = n2
        n2.next = n1

        assert is_reconstructible(n1) and is_reconstructible(n2)

    @pytest.mark.skip(reason="currently not implemented")
    def test_pd_dataframe(self):
        df = pd.DataFrame({"x": [1, 2, 3, 4]})
        assert is_reconstructible(df)

    def test_int(self):
        i = 1
        assert is_reconstructible(i)

    @pytest.mark.skip(reason="currently not implemented")
    def test_file(self, tmp_path):
        with open(tmp_path / "test.txt", "w") as f:
            assert not is_reconstructible(f)
