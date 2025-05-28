import ast
from ast import *

import pytest

from src.explotest.pytest_fixture import PyTestFixture


def pickle_mode_body() -> list[AST]:
    return [With(items=[withitem(context_expr=Call(func=Name(id='open', ctx=Load()), args=[Constant(value='foo.pkl')]),
                                 optional_vars=Name(id='f', ctx=Store()))], body=[Return(
        value=Call(func=Attribute(value=Name(id='dill', ctx=Load()), attr='load', ctx=Load()),
                   args=[Name(id='f', ctx=Load())]))])]


def sample_arg_reconstruct_body() -> list[AST]:
    initialize_x = Assign(targets=[Name(id='x', ctx=Store())], value=Call(func=Name(id='Foo', ctx=Load())))
    set_attr_of_x = Assign(targets=[Attribute(value=Name(id='x', ctx=Load()), attr='y', ctx=Store())],
                           value=Constant(value='Meow!'))
    return_x = Return(value=Name(id='x', ctx=Load()))
    return [initialize_x, set_attr_of_x, return_x]


@pytest.mark.parametrize('var_name', ['x', 'y', 'z', 'f3', '_sample'])
@pytest.mark.parametrize('body', [pickle_mode_body(), sample_arg_reconstruct_body()])
class TestFixtureGeneration:
    def test_fixture_contains_correct_body(self, body, var_name):
        """
        This test tests that the body supplied is correctly injected into the new fixture.
        """
        result = PyTestFixture([], var_name, body)
        expected = FunctionDef(name=f'generate_{var_name}', args=arguments(), body=body,
            decorator_list=[Attribute(value=Name(id='pytest', ctx=Load()), attr='fixture', ctx=Load())])

        assert ast.unparse(ast.fix_missing_locations(expected)) == ast.unparse(result.ast_node)

    def test_fixture_resolves_dependencies(self, var_name, body):
        """
        Tests that the Fixture class correctly requests its dependent fixtures.
        """

        """
        ->: depends on
        Case: x -> abstract_factory_proxy_bean_singleton, kevin_liu
        """
        depend_abstract_factory_proxy_bean_singleton = PyTestFixture([], 'abstract_factory_proxy_bean_singleton',
                                                                     [Pass()])
        depend_kevin_liu = PyTestFixture([], 'kevin_liu', [Pass()])

        result_with_depends = PyTestFixture([depend_abstract_factory_proxy_bean_singleton, depend_kevin_liu], var_name,
                                            body)

        args_as_string = [arg.arg for arg in result_with_depends.ast_node.args.args]

        assert f'generate_{depend_abstract_factory_proxy_bean_singleton.parameter}' in args_as_string
        assert f'generate_{depend_kevin_liu.parameter}' in args_as_string

    # def test_
