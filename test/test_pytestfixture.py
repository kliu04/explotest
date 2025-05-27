import ast
from ast import *

from src.prototype_ipy_explotest.generated_test import PyTestFixture


def test_ast_node_generation() -> None:
    fixture1 = PyTestFixture('foo')
    l1 = Call(func=Name(id='print', ctx=Load()), args=[
        Call(func=Attribute(value=Name(id='ast', ctx=Load()), attr='dump', ctx=Load()), args=[
            Call(func=Attribute(value=Name(id='ast', ctx=Load()), attr='parse', ctx=Load()),
                 args=[Constant(value="print('hello, world!')")])],
             keywords=[keyword(arg='indent', value=Constant(value=4))])])
    l2 = Assign(targets=[Name(id='x', ctx=Store())], value=Constant(value=3))
    l3 = If(test=Compare(left=Name(id='x', ctx=Load()), ops=[GtE()], comparators=[Constant(value=3)]),
            body=[Return(value=Constant(value=1))])
    fixture1.add_node(l1)
    fixture1.add_node(l2)
    fixture1.add_node(l3)

    fixture2 = PyTestFixture('bar')
    fixture2.add_node(Return(value=Constant(value='meow :3')))

    fixture1.add_depends(fixture2)

    expected_test_node = FunctionDef(name='generated_foo', args=arguments(args=[arg('generated_bar')]),
                                     body=[l1, l2, l3], decorator_list=[
            Attribute(value=Name(id='pytest', ctx=Load()), attr='fixture', ctx=Load())
        ])

    expected_test_node = ast.fix_missing_locations(expected_test_node)

    assert ast.unparse(expected_test_node) == ast.unparse(fixture1.ast_node)



