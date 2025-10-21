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

    tb.build_imports(None).build_fixtures(ArgumentReconstructor(tmp_path)).build_act_phase(sig)

    assert tb.parameters == ["x", "y", "z", "bar", "baz"]
    assert tb.arguments == [1, 2, 3, 7, 6]

    mt = tb.get_meta_test()
    assert len(mt.direct_fixtures) == 5
    
    # Verify fixture parameters match
    for i, (param, value) in enumerate(zip(["x", "y", "z", "bar", "baz"], [1, 2, 3, 7, 6])):
        assert mt.direct_fixtures[i].parameter == param
    
    # Verify act phase is correct
    assert mt.act_phase is not None
    call = mt.act_phase.value
    # Should have 3 positional args (x, y, z)
    assert len(call.args) == 3
    # Should have 2 keyword args (bar, baz)
    assert len(call.keywords) == 2
    keyword_names = [kw.arg for kw in call.keywords]
    assert "bar" in keyword_names
    assert "baz" in keyword_names


def test_test_builder_mixed_args_kwargs(tmp_path):
    """Test TestBuilder with positional, *args, keyword-only, and **kwargs."""
    def example_func(x, y, z=0, *args, bar, baz, **kwargs):
        pass

    sig = inspect.signature(example_func)

    bound_args = sig.bind(1, 2, 3, 4, 5, baz=6, bar=7, kwarg1=True, kwarg2=False)
    tb = TestBuilder(tmp_path, "fut", dict(bound_args.arguments))

    tb.build_imports(None).build_fixtures(ArgumentReconstructor(tmp_path)).build_act_phase(sig)

    assert tb.parameters == ["x", "y", "z", "args", "bar", "baz", "kwargs"]
    assert tb.arguments == [1, 2, 3, (4, 5), 7, 6, {"kwarg1": True, "kwarg2": False}]

    mt = tb.get_meta_test()
    assert len(mt.direct_fixtures) == 7
    
    # Verify fixture parameters
    expected_params = ["x", "y", "z", "args", "bar", "baz", "kwargs"]
    for i, param in enumerate(expected_params):
        assert mt.direct_fixtures[i].parameter == param
    
    # Verify act phase structure
    assert mt.act_phase is not None
    call = mt.act_phase.value
    # Should have 3 positional args + 1 *args = 4 total in args list
    assert len(call.args) == 4
    # Check that the 4th arg is a Starred node (for *args)
    import ast
    assert isinstance(call.args[3], ast.Starred)
    # Should have 2 keyword-only args (bar, baz) + 1 **kwargs = 3 keywords
    assert len(call.keywords) == 3
    # Check keyword-only args
    keyword_only = [kw for kw in call.keywords if kw.arg is not None]
    assert len(keyword_only) == 2
    keyword_names = [kw.arg for kw in keyword_only]
    assert "bar" in keyword_names
    assert "baz" in keyword_names
    # Check **kwargs (has arg=None)
    kwargs_kw = [kw for kw in call.keywords if kw.arg is None]
    assert len(kwargs_kw) == 1


def test_test_builder_only_keyword_args(tmp_path):
    """Test TestBuilder with only keyword-only arguments."""
    def example_func(*, bar, baz):
        pass

    sig = inspect.signature(example_func)

    bound_args = sig.bind(bar=42, baz=100)
    tb = TestBuilder(tmp_path, "fut", dict(bound_args.arguments))

    tb.build_imports(None).build_fixtures(ArgumentReconstructor(tmp_path)).build_act_phase(sig)

    assert tb.parameters == ["bar", "baz"]
    assert tb.arguments == [42, 100]

    mt = tb.get_meta_test()
    assert len(mt.direct_fixtures) == 2
    
    # Verify fixtures
    assert mt.direct_fixtures[0].parameter == "bar"
    assert mt.direct_fixtures[1].parameter == "baz"
    
    # Verify act phase - should have NO positional args, only keyword args
    assert mt.act_phase is not None
    call = mt.act_phase.value
    assert len(call.args) == 0  # No positional args
    assert len(call.keywords) == 2  # Two keyword args
    keyword_names = [kw.arg for kw in call.keywords]
    assert "bar" in keyword_names
    assert "baz" in keyword_names


def test_test_builder_only_varargs(tmp_path):
    """Test TestBuilder with only *args."""
    def example_func(*args):
        pass

    sig = inspect.signature(example_func)

    bound_args = sig.bind(1, 2, 3, 4, 5)
    tb = TestBuilder(tmp_path, "fut", dict(bound_args.arguments))

    tb.build_imports(None).build_fixtures(ArgumentReconstructor(tmp_path)).build_act_phase(sig)

    assert tb.parameters == ["args"]
    assert tb.arguments == [(1, 2, 3, 4, 5)]

    mt = tb.get_meta_test()
    assert len(mt.direct_fixtures) == 1
    assert mt.direct_fixtures[0].parameter == "args"
    
    # Verify act phase - should have 1 Starred arg
    assert mt.act_phase is not None
    call = mt.act_phase.value
    assert len(call.args) == 1
    import ast
    assert isinstance(call.args[0], ast.Starred)
    assert len(call.keywords) == 0  # No keyword args


def test_test_builder_only_kwargs(tmp_path):
    """Test TestBuilder with only **kwargs."""
    def example_func(**kwargs):
        pass

    sig = inspect.signature(example_func)

    bound_args = sig.bind(x=10, y=20, z=30)
    tb = TestBuilder(tmp_path, "fut", dict(bound_args.arguments))

    tb.build_imports(None).build_fixtures(ArgumentReconstructor(tmp_path)).build_act_phase(sig)

    assert tb.parameters == ["kwargs"]
    assert tb.arguments == [{"x": 10, "y": 20, "z": 30}]

    mt = tb.get_meta_test()
    assert len(mt.direct_fixtures) == 1
    assert mt.direct_fixtures[0].parameter == "kwargs"
    
    # Verify act phase - should have NO positional args, only **kwargs
    assert mt.act_phase is not None
    call = mt.act_phase.value
    assert len(call.args) == 0  # No positional args
    assert len(call.keywords) == 1  # One **kwargs
    assert call.keywords[0].arg is None  # **kwargs has arg=None


def test_test_builder_complex_signature_from_demo(tmp_path):
    """Test TestBuilder with complex signature from args_kwargs demo.
    
    This matches the signature: foo1(x, y, z, *args, bar, baz, **kwargs)
    called as: foo1(1, 2, 3, 4, 5, baz=6, bar=7, kwarg1=True, kwarg2=False)
    """
    def example_func(x, y, z, *args, bar, baz, **kwargs):
        pass

    sig = inspect.signature(example_func)

    bound_args = sig.bind(1, 2, 3, 4, 5, baz=6, bar=7, kwarg1=True, kwarg2=False)
    tb = TestBuilder(tmp_path, "fut", dict(bound_args.arguments))

    tb.build_imports(None).build_fixtures(ArgumentReconstructor(tmp_path)).build_act_phase(sig)

    # Verify parameters and arguments match expectations
    assert tb.parameters == ["x", "y", "z", "args", "bar", "baz", "kwargs"]
    assert tb.arguments == [1, 2, 3, (4, 5), 7, 6, {"kwarg1": True, "kwarg2": False}]

    mt = tb.get_meta_test()
    assert len(mt.direct_fixtures) == 7
    
    # Verify all fixtures have correct parameters
    expected_params = ["x", "y", "z", "args", "bar", "baz", "kwargs"]
    for i, param in enumerate(expected_params):
        assert mt.direct_fixtures[i].parameter == param
    
    # Verify act phase structure matches the complex signature
    assert mt.act_phase is not None
    call = mt.act_phase.value
    # Should have 3 positional (x, y, z) + 1 *args = 4 in args list
    assert len(call.args) == 4
    import ast
    # Check the 4th is Starred for *args
    assert isinstance(call.args[3], ast.Starred)
    # Should have 2 keyword-only (bar, baz) + 1 **kwargs = 3 keywords
    assert len(call.keywords) == 3
    # Verify keyword-only parameters
    keyword_only = [kw for kw in call.keywords if kw.arg is not None]
    assert len(keyword_only) == 2
    keyword_names = [kw.arg for kw in keyword_only]
    assert "bar" in keyword_names
    assert "baz" in keyword_names
    # Verify **kwargs present
    kwargs_kw = [kw for kw in call.keywords if kw.arg is None]
    assert len(kwargs_kw) == 1
