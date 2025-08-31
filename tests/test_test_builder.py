import inspect

from explotest.reconstructors.argument_reconstructor import ArgumentReconstructor
from explotest.test_builder import TestBuilder


def test_test_builder_1(tmp_path):
    def example_func(a, b, c=3, *args, **kwargs):
        pass
    sig = inspect.signature(example_func)

    bound_args = sig.bind(10, 20, 30, 40, 50, x=100, y=200)
    tb = TestBuilder("fut", tmp_path, bound_args, ArgumentReconstructor)
    
    assert (built := tb.build_test())
    
    assert built.fut_name == "fut"
    assert built.fut_parameters == ['a', 'b', 'c', 'args', 'kwargs']
    
    assert len(built.direct_fixtures) == 5
    
    