import ast
from typing import cast

from explotest.meta_fixture import MetaFixture
from explotest.meta_test import MetaTest


def ast_equal(a: ast.AST, b: ast.AST) -> bool:
    """Check if two ASTs are structurally equivalent."""
    return ast.dump(ast.parse(ast.unparse(a))) == ast.dump(ast.parse(ast.unparse(b)))


def test_meta_test_1():
    mf_body = ast.parse("x = 1")
    mf_ret = ast.parse("return x")
    fixture_x = MetaFixture([], "x", cast(list[ast.stmt], [mf_body]), cast(ast.Return, mf_ret))

    mf_body = [ast.parse("y = 42", mode="exec").body[0]]
    mf_ret = ast.Return(value=ast.Name(id="y", ctx=ast.Load()))
    fixture_y = MetaFixture(depends=[], parameter="y", body=mf_body, ret=mf_ret)

    # return_value = foo(x, y)
    call_node = ast.Assign(
        targets=[ast.Name(id="return_value", ctx=ast.Store())],
        value=ast.Call(
            func=ast.Name(id="foo", ctx=ast.Load()),
            args=[
                ast.Name(id="x", ctx=ast.Load()),
                ast.Name(id="y", ctx=ast.Load())
            ],
            keywords=[]
        )
    )

    # assert return_value == 1
    assert_node = ast.Assert(
        test=ast.Compare(
            left=ast.Name(id="return_value", ctx=ast.Load()),
            ops=[ast.Eq()],
            comparators=[ast.Constant(value=1)]
        ),
        msg=None
    )

    mt = MetaTest()
    mt.fut_name = "fut"
    mt.fut_parameters = ["x", "y"]
    mt.imports = [ast.Import([ast.alias("bar")])]
    mt.direct_fixtures = [fixture_x, fixture_y]
    mt.act_phase = call_node
    mt.asserts = [assert_node]

    # assert mt._make_main_function().args == ast.arguments()
    assert (
        ast.unparse(
            ast.parse(
                """import bar

@pytest.fixture
def generate_x():
    x = 1
    return x

@pytest.fixture
def generate_y():
    y = 42
    return y

def test_fut(generate_x, generate_y):
    x = generate_x
    y = generate_y
    return_value = foo(x, y)
    assert return_value == 1
    """
            )
        )
        == ast.unparse(mt.make_test())
    )
