import pytest
from ast import *

def test_test_function_creation() -> None:
    expected = FunctionDef(name='test_foo', args=arguments(args=[arg('foo')]),
                           body=[Assign(targets=[Name(id='result', ctx=Store())],
                                        value=Call(func=Name(id='bar', ctx=Load())))])

    # generated_test =