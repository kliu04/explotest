from ast import *

from src.prototype_ipy_explotest.generated_test import GeneratedTest, PyTestFixture


def test_test_function_creation() -> None:
    """
    Expected:
    def test_foo(generated_bar):
        result = foo(generated_bar)
    """
    expected = FunctionDef(name='test_foo', args=arguments(args=[arg('generated_bar')]), body=[
        Assign(targets=[Name(id='result', ctx=Store())],
               value=Call(func=Name(id='bar', ctx=Load()), args=[Name(id='generated_bar', ctx=Load())]))])
    expected = fix_missing_locations(expected)

    fixture = PyTestFixture('bar')
    fixture.add_node(Return(value=Constant(value=3)))

    t = GeneratedTest([], set(), 'foo', [fixture], [Assign(targets=[Name(id='result', ctx=Store())],
                                                           value=Call(func=Name(id='bar', ctx=Load()),
                                                                      args=[Name(id='generated_bar', ctx=Load())]))],
                      [])

    assert unparse(expected) == unparse(t.test_function)
