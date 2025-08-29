import ast
from ast import *

import pytest

from src.explotest.meta_fixture import MetaFixture


def pickle_mode_body() -> list[AST]:
    return [With(items=[withitem(context_expr=Call(func=Name(id='open', ctx=Load()), args=[Constant(value='foo.pkl')]),
                                 optional_vars=Name(id='f', ctx=Store()))], body=[
        Assign(targets=[Name(id='x', ctx=Store())],
            value=Call(func=Attribute(value=Name(id='dill', ctx=Load()), attr='loads', ctx=Load()),
                args=[Constant(value='test_string')]))])]


def sample_arg_reconstruct_body() -> list[AST]:
    initialize_x = Assign(targets=[Name(id='x', ctx=Store())], value=Call(func=Name(id='Foo', ctx=Load())))
    set_attr_of_x = Assign(targets=[Attribute(value=Name(id='x', ctx=Load()), attr='y', ctx=Store())],
                           value=Constant(value='Meow!'))

    return [initialize_x, set_attr_of_x]


def sample_arg_reconstruct_return() -> Return:
    return_x = Return(value=Name(id='x', ctx=Load()))
    return return_x


def pickle_mode_return() -> Return:
    return Return(value=Name(id='x', ctx=Load()))


@pytest.mark.parametrize('var_name', ['x', 'y', 'z', 'f3', '_sample'])
@pytest.mark.parametrize('body', [pickle_mode_body(), sample_arg_reconstruct_body()])
@pytest.mark.parametrize('ret', [pickle_mode_return(), sample_arg_reconstruct_return()])
class TestFixtureGeneration:
    def test_fixture_contains_correct_body(self, var_name, body, ret):
        """
        This test tests that the body supplied is correctly injected into the new fixture.
        """
        result = MetaFixture([], var_name, body, ret)
        expected = FunctionDef(name=f'generate_{var_name}', args=arguments(), body=body + [ret], decorator_list=[
            Attribute(value=Name(id='pytest', ctx=Load()), attr='fixture', ctx=Load())])


        assert ast.unparse(ast.fix_missing_locations(expected)) == ast.unparse(result.make_fixture)

    def test_fixture_resolves_dependencies(self, var_name, body, ret):
        """
        Tests that the Fixture class correctly requests its dependent fixtures.
        """

        """
        ->: depends on
        Case: x -> abstract_factory_proxy_bean_singleton, kevin_liu
        """
        depend_abstract_factory_proxy_bean_singleton = MetaFixture([], 'abstract_factory_proxy_bean_singleton',
                                                                   [Pass()], Return(value=Constant(value=None)))
        depend_kevin_liu = MetaFixture([], 'kevin_liu', [Pass()], Return(value=Constant(value=None)))

        result_with_depends = MetaFixture([depend_abstract_factory_proxy_bean_singleton, depend_kevin_liu], var_name,
                                          body, Return(value=Constant(value=None)))

        args_as_string = [arg.arg for arg in result_with_depends.make_fixture.args.args]

        assert f'generate_{depend_abstract_factory_proxy_bean_singleton.parameter}' in args_as_string
        assert f'generate_{depend_kevin_liu.parameter}' in args_as_string
