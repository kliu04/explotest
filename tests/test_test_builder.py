import inspect

from explotest.reconstructors.argument_reconstructor import ArgumentReconstructor
from explotest.test_builder import TestBuilder


def test_test_builder_1(tmp_path):
    def example_func(a, b, c=30, *args, **kwargs):
        pass

    sig = inspect.signature(example_func)

    bound_args = sig.bind(10, 20, 30, 40, 50, x=100, y=200)
    tb = TestBuilder(tmp_path, "fut", dict(bound_args.arguments))

    tb.build_imports(None).build_fixtures(ArgumentReconstructor(tmp_path))

    assert tb.parameters == ["a", "b", "c", "args", "kwargs"]
    assert tb.arguments == [10, 20, 30, (40, 50), {"x": 100, "y": 200}]

    mt = tb.get_meta_test()

    assert len(mt.direct_fixtures) == 5


def test_test_builder_2(tmp_path):
    def example_func(a, b, c=30):
        pass

    sig = inspect.signature(example_func)

    bound_args = sig.bind(10, 20)
    tb = TestBuilder(tmp_path, "fut", dict(bound_args.arguments))

    tb.build_imports(None).build_fixtures(ArgumentReconstructor(tmp_path))

    assert tb.parameters == ["a", "b"]
    assert tb.arguments == [10, 20]


def test_test_builder_keyword_only(tmp_path):
    """Test TestBuilder with keyword-only arguments."""
    def example_func(x, y, z, *, bar, baz):
        pass

    sig = inspect.signature(example_func)

    bound_args = sig.bind(1, 2, 3, bar=7, baz=6)
    tb = TestBuilder(tmp_path, "fut", dict(bound_args.arguments))

    tb.build_imports(None).build_fixtures(ArgumentReconstructor(tmp_path))

    assert tb.parameters == ["x", "y", "z", "bar", "baz"]
    assert tb.arguments == [1, 2, 3, 7, 6]

    mt = tb.get_meta_test()
    assert len(mt.direct_fixtures) == 5


def test_test_builder_mixed_args_kwargs(tmp_path):
    """Test TestBuilder with positional, *args, keyword-only, and **kwargs."""
    def example_func(x, y, z=0, *args, bar, baz, **kwargs):
        pass

    sig = inspect.signature(example_func)

    bound_args = sig.bind(1, 2, 3, 4, 5, baz=6, bar=7, kwarg1=True, kwarg2=False)
    tb = TestBuilder(tmp_path, "fut", dict(bound_args.arguments))

    tb.build_imports(None).build_fixtures(ArgumentReconstructor(tmp_path))

    assert tb.parameters == ["x", "y", "z", "args", "bar", "baz", "kwargs"]
    assert tb.arguments == [1, 2, 3, (4, 5), 7, 6, {"kwarg1": True, "kwarg2": False}]

    mt = tb.get_meta_test()
    assert len(mt.direct_fixtures) == 7


def test_test_builder_only_keyword_args(tmp_path):
    """Test TestBuilder with only keyword-only arguments."""
    def example_func(*, bar, baz):
        pass

    sig = inspect.signature(example_func)

    bound_args = sig.bind(bar=42, baz=100)
    tb = TestBuilder(tmp_path, "fut", dict(bound_args.arguments))

    tb.build_imports(None).build_fixtures(ArgumentReconstructor(tmp_path))

    assert tb.parameters == ["bar", "baz"]
    assert tb.arguments == [42, 100]

    mt = tb.get_meta_test()
    assert len(mt.direct_fixtures) == 2


def test_test_builder_only_varargs(tmp_path):
    """Test TestBuilder with only *args."""
    def example_func(*args):
        pass

    sig = inspect.signature(example_func)

    bound_args = sig.bind(1, 2, 3, 4, 5)
    tb = TestBuilder(tmp_path, "fut", dict(bound_args.arguments))

    tb.build_imports(None).build_fixtures(ArgumentReconstructor(tmp_path))

    assert tb.parameters == ["args"]
    assert tb.arguments == [(1, 2, 3, 4, 5)]

    mt = tb.get_meta_test()
    assert len(mt.direct_fixtures) == 1


def test_test_builder_only_kwargs(tmp_path):
    """Test TestBuilder with only **kwargs."""
    def example_func(**kwargs):
        pass

    sig = inspect.signature(example_func)

    bound_args = sig.bind(x=10, y=20, z=30)
    tb = TestBuilder(tmp_path, "fut", dict(bound_args.arguments))

    tb.build_imports(None).build_fixtures(ArgumentReconstructor(tmp_path))

    assert tb.parameters == ["kwargs"]
    assert tb.arguments == [{"x": 10, "y": 20, "z": 30}]

    mt = tb.get_meta_test()
    assert len(mt.direct_fixtures) == 1
