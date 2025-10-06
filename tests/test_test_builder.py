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
