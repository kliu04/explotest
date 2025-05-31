from pytest import fixture

from src.explotest.argument_reconstruction_reconstructor import (
    ArgumentReconstructionReconstructor,
)


@fixture
def setup(tmp_path):
    arr = ArgumentReconstructionReconstructor(tmp_path)
    return arr


def test_reconstruct_object_instance(setup):
    class Foo:
        x = 1
        y = 2

    setup.asts({"x": Foo()})

    """
    x = Foo.__new__(Foo)
    setattr(x, x, 1)
    setattr(x, y, 2)
    """


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
