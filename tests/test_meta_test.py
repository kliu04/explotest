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
    fixture_x = MetaFixture(
        [], "x", cast(list[ast.stmt], [mf_body]), cast(ast.Return, mf_ret)
    )

    mf_body = [ast.parse("y = 42", mode="exec").body[0]]
    mf_ret = ast.Return(value=ast.Name(id="y", ctx=ast.Load()))
    fixture_y = MetaFixture(depends=[], parameter="y", body=mf_body, ret=mf_ret)

    # return_value = foo(x, y)
    call_node = ast.Assign(
        targets=[ast.Name(id="return_value", ctx=ast.Store())],
        value=ast.Call(
            func=ast.Name(id="foo", ctx=ast.Load()),
            args=[ast.Name(id="x", ctx=ast.Load()), ast.Name(id="y", ctx=ast.Load())],
            keywords=[],
        ),
    )

    # assert return_value == 1
    assert_node = ast.Assert(
        test=ast.Compare(
            left=ast.Name(id="return_value", ctx=ast.Load()),
            ops=[ast.Eq()],
            comparators=[ast.Constant(value=1)],
        ),
        msg=None,
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


def test_meta_test_with_keyword_params():
    """Test MetaTest with keyword-only parameters."""
    # Create fixtures for keyword-only parameters
    mf_body = [ast.parse("bar = 10", mode="exec").body[0]]
    mf_ret = ast.Return(value=ast.Name(id="bar", ctx=ast.Load()))
    fixture_bar = MetaFixture(depends=[], parameter="bar", body=mf_body, ret=mf_ret)

    mf_body = [ast.parse("baz = 20", mode="exec").body[0]]
    mf_ret = ast.Return(value=ast.Name(id="baz", ctx=ast.Load()))
    fixture_baz = MetaFixture(depends=[], parameter="baz", body=mf_body, ret=mf_ret)

    # return_value = func(bar=bar, baz=baz)
    call_node = ast.Assign(
        targets=[ast.Name(id="return_value", ctx=ast.Store())],
        value=ast.Call(
            func=ast.Name(id="func", ctx=ast.Load()),
            args=[],
            keywords=[
                ast.keyword(arg="bar", value=ast.Name(id="bar", ctx=ast.Load())),
                ast.keyword(arg="baz", value=ast.Name(id="baz", ctx=ast.Load())),
            ],
        ),
    )

    # assert return_value == 30
    assert_node = ast.Assert(
        test=ast.Compare(
            left=ast.Name(id="return_value", ctx=ast.Load()),
            ops=[ast.Eq()],
            comparators=[ast.Constant(value=30)],
        ),
        msg=None,
    )

    mt = MetaTest()
    mt.fut_name = "test_func"
    mt.fut_parameters = ["bar", "baz"]
    mt.imports = [ast.Import([ast.alias("pytest")])]
    mt.direct_fixtures = [fixture_bar, fixture_baz]
    mt.act_phase = call_node
    mt.asserts = [assert_node]

    generated = mt.make_test()
    assert generated is not None
    assert isinstance(generated, ast.Module)
    assert len(generated.body) == 4  # import + 2 fixtures + test function


def test_meta_test_with_multiple_asserts():
    """Test MetaTest with multiple assertions."""
    mf_body = [ast.parse("x = 5", mode="exec").body[0]]
    mf_ret = ast.Return(value=ast.Name(id="x", ctx=ast.Load()))
    fixture_x = MetaFixture(depends=[], parameter="x", body=mf_body, ret=mf_ret)

    # return_value = foo(x)
    call_node = ast.Assign(
        targets=[ast.Name(id="return_value", ctx=ast.Store())],
        value=ast.Call(
            func=ast.Name(id="foo", ctx=ast.Load()),
            args=[ast.Name(id="x", ctx=ast.Load())],
            keywords=[],
        ),
    )

    # Multiple assertions
    assert_node_1 = ast.Assert(
        test=ast.Compare(
            left=ast.Name(id="return_value", ctx=ast.Load()),
            ops=[ast.Gt()],
            comparators=[ast.Constant(value=0)],
        ),
        msg=None,
    )

    assert_node_2 = ast.Assert(
        test=ast.Compare(
            left=ast.Name(id="return_value", ctx=ast.Load()),
            ops=[ast.Lt()],
            comparators=[ast.Constant(value=10)],
        ),
        msg=None,
    )

    mt = MetaTest()
    mt.fut_name = "foo"
    mt.fut_parameters = ["x"]
    mt.imports = [ast.Import([ast.alias("pytest")])]
    mt.direct_fixtures = [fixture_x]
    mt.act_phase = call_node
    mt.asserts = [assert_node_1, assert_node_2]

    generated = mt.make_test()
    assert generated is not None
    assert isinstance(generated, ast.Module)
    # Check that the test function contains both assertions
    test_func = generated.body[-1]
    assert isinstance(test_func, ast.FunctionDef)
    assert len(test_func.body) == 4  # x = generate_x, call, assert1, assert2


def test_meta_test_with_no_params():
    """Test MetaTest with no parameters."""
    # return_value = func()
    call_node = ast.Assign(
        targets=[ast.Name(id="return_value", ctx=ast.Store())],
        value=ast.Call(
            func=ast.Name(id="func", ctx=ast.Load()),
            args=[],
            keywords=[],
        ),
    )

    # assert return_value is not None
    assert_node = ast.Assert(
        test=ast.Compare(
            left=ast.Name(id="return_value", ctx=ast.Load()),
            ops=[ast.IsNot()],
            comparators=[ast.Constant(value=None)],
        ),
        msg=None,
    )

    mt = MetaTest()
    mt.fut_name = "func"
    mt.fut_parameters = []
    mt.imports = [ast.Import([ast.alias("pytest")])]
    mt.direct_fixtures = []
    mt.act_phase = call_node
    mt.asserts = [assert_node]

    generated = mt.make_test()
    assert generated is not None
    assert isinstance(generated, ast.Module)
    # Should have import + test function (no fixtures)
    assert len(generated.body) == 2


def test_meta_test_with_fixture_dependencies():
    """Test MetaTest with fixtures that have dependencies."""
    # Create a fixture with a dependency
    dep_body = [ast.parse("base = 100", mode="exec").body[0]]
    dep_ret = ast.Return(value=ast.Name(id="base", ctx=ast.Load()))
    dep_fixture = MetaFixture(depends=[], parameter="base", body=dep_body, ret=dep_ret)

    body = [ast.parse("x = base * 2", mode="exec").body[0]]
    ret = ast.Return(value=ast.Name(id="x", ctx=ast.Load()))
    fixture_x = MetaFixture(depends=[dep_fixture], parameter="x", body=body, ret=ret)

    # return_value = foo(x)
    call_node = ast.Assign(
        targets=[ast.Name(id="return_value", ctx=ast.Store())],
        value=ast.Call(
            func=ast.Name(id="foo", ctx=ast.Load()),
            args=[ast.Name(id="x", ctx=ast.Load())],
            keywords=[],
        ),
    )

    # assert return_value == 200
    assert_node = ast.Assert(
        test=ast.Compare(
            left=ast.Name(id="return_value", ctx=ast.Load()),
            ops=[ast.Eq()],
            comparators=[ast.Constant(value=200)],
        ),
        msg=None,
    )

    mt = MetaTest()
    mt.fut_name = "foo"
    mt.fut_parameters = ["x"]
    mt.imports = [ast.Import([ast.alias("pytest")])]
    mt.direct_fixtures = [fixture_x]
    mt.act_phase = call_node
    mt.asserts = [assert_node]

    generated = mt.make_test()
    assert generated is not None
    assert isinstance(generated, ast.Module)
    # Should have import + fixture_x (which includes base) + test function
    # fixture_x.make_fixture() returns [fixture_x, base_fixture]
    assert len(generated.body) == 3  # import + [fixture_x, base_fixture] + test function


