import inspect

from explotest.reconstructors.argument_reconstructor import ArgumentReconstructor
from explotest.test_builder import TestBuilder


def test_test_builder_1(tmp_path):
    def example_func(a, b, c=3, *args, **kwargs):
        pass

    sig = inspect.signature(example_func)

    bound_args = sig.bind(10, 20, 30, 40, 50, x=100, y=200)
    tb = TestBuilder(tmp_path, "fut", dict(bound_args.arguments))

    tb.build_imports(None).build_fixtures(ArgumentReconstructor(tmp_path))

    assert tb.fut_name == "fut"
    assert tb.parameters == ["a", "b", "c", "args", "kwargs"]

    mt = tb.get_meta_test()

    assert len(mt.direct_fixtures) == 5
