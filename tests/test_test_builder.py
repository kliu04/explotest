import ast
import inspect

from explotest.reconstructors.argument_reconstructor import ArgumentReconstructor
from explotest.test_builder import TestBuilder


def test_test_builder_1(tmp_path):
    def example_func(a, b, c=30, *args, **kwargs):
        pass

    sig = inspect.signature(example_func)

    bound_args = sig.bind(10, 20, 30, 40, 50, x=100, y=200)
    tb = TestBuilder(tmp_path, "fut", dict(bound_args.arguments), sig)

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
    tb = TestBuilder(tmp_path, "fut", dict(bound_args.arguments), sig)

    tb.build_imports(None).build_fixtures(ArgumentReconstructor(tmp_path))

    assert tb.parameters == ["a", "b"]
    assert tb.arguments == [10, 20]


def test_test_builder_args_kwargs_unpacking(tmp_path):
    """Test that *args and **kwargs are properly unpacked in the generated AST call"""
    def example_func(a, b, c=30, *args, **kwargs):
        pass

    sig = inspect.signature(example_func)
    bound_args = sig.bind(10, 20, 30, 40, 50, x=100, y=200)
    
    tb = TestBuilder(tmp_path, "example_func", dict(bound_args.arguments), sig)
    tb.build_act_phase()
    
    # Get the generated AST and unparse it
    act_phase = tb.get_meta_test().act_phase
    generated_code = ast.unparse(act_phase)
    
    # Verify that args and kwargs are unpacked with * and **
    assert "*args" in generated_code, "args should be unpacked with *"
    assert "**kwargs" in generated_code, "kwargs should be unpacked with **"
    # Ensure they're not just passed as regular parameters
    assert "args, kwargs)" not in generated_code, "args and kwargs should not be passed as regular parameters"


def test_test_builder_kwargs_only_unpacking(tmp_path):
    """Test that **kwargs is properly unpacked when there's no *args"""
    def example_func(a, b, **kwargs):
        pass

    sig = inspect.signature(example_func)
    bound_args = sig.bind(10, 20, x=100, y=200)
    
    tb = TestBuilder(tmp_path, "example_func", dict(bound_args.arguments), sig)
    tb.build_act_phase()
    
    act_phase = tb.get_meta_test().act_phase
    generated_code = ast.unparse(act_phase)
    
    assert "**kwargs" in generated_code, "kwargs should be unpacked with **"
    assert "*args" not in generated_code, "should not have *args when not in signature"


def test_test_builder_args_only_unpacking(tmp_path):
    """Test that *args is properly unpacked when there's no **kwargs"""
    def example_func(a, b, *args):
        pass

    sig = inspect.signature(example_func)
    bound_args = sig.bind(10, 20, 30, 40)
    
    tb = TestBuilder(tmp_path, "example_func", dict(bound_args.arguments), sig)
    tb.build_act_phase()
    
    act_phase = tb.get_meta_test().act_phase
    generated_code = ast.unparse(act_phase)
    
    assert "*args" in generated_code, "args should be unpacked with *"
    assert "**kwargs" not in generated_code, "should not have **kwargs when not in signature"


def test_test_builder_no_unpacking(tmp_path):
    """Test that regular parameters are passed without unpacking"""
    def example_func(a, b, c):
        pass

    sig = inspect.signature(example_func)
    bound_args = sig.bind(10, 20, 30)
    
    tb = TestBuilder(tmp_path, "example_func", dict(bound_args.arguments), sig)
    tb.build_act_phase()
    
    act_phase = tb.get_meta_test().act_phase
    generated_code = ast.unparse(act_phase)
    
    assert "*" not in generated_code, "should not have any unpacking for regular parameters"


def test_test_builder_custom_varargs_names(tmp_path):
    """Test that variadic arguments work with custom names (not just 'args' and 'kwargs')"""
    def example_func(a, b, *items, **options):
        pass

    sig = inspect.signature(example_func)
    bound_args = sig.bind(10, 20, 30, 40, x=100, y=200)
    
    tb = TestBuilder(tmp_path, "example_func", dict(bound_args.arguments), sig)
    tb.build_act_phase()
    
    act_phase = tb.get_meta_test().act_phase
    generated_code = ast.unparse(act_phase)
    
    # Verify that custom names are unpacked correctly
    assert "*items" in generated_code, "items should be unpacked with *"
    assert "**options" in generated_code, "options should be unpacked with **"
    # Ensure they're not passed as regular parameters
    assert "items, options)" not in generated_code, "items and options should not be passed as regular parameters"
