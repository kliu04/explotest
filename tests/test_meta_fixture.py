import ast
from typing import cast

from explotest.meta_fixture import MetaFixture


def ast_equal(a: ast.AST, b: ast.AST) -> bool:
    """Check if two ASTs are structurally equivalent."""
    return ast.dump(ast.parse(ast.unparse(a))) == ast.dump(ast.parse(ast.unparse(b)))

def test_make_fixture_1():
    mf_body = ast.parse("x = 1")
    mf_ret = ast.parse("return x")
    mf = MetaFixture([], "x", cast(list[ast.stmt], [mf_body]), cast(ast.Return, mf_ret))

    constructed_fixtures = mf.make_fixture()
    assert len(constructed_fixtures) == 1

    generated_fun = constructed_fixtures[0]

    expected_code = """
@pytest.fixture
def generate_x():
    x = 1
    return x
"""
    expected_ast = ast.parse(expected_code, mode="exec")

    assert ast_equal(generated_fun, expected_ast)

def test_make_fixture_2():
    dep_body = [ast.parse("y = 42", mode="exec").body[0]]
    dep_ret = ast.Return(value=ast.Name(id="y", ctx=ast.Load()))
    dep = MetaFixture(depends=[], parameter="y", body=dep_body, ret=dep_ret)

    body = [ast.parse("x = y + 1", mode="exec").body[0]]
    ret = ast.Return(value=ast.Name(id="x", ctx=ast.Load()))
    mf = MetaFixture(depends=[dep], parameter="x", body=body, ret=ret)

    generated_list = mf.make_fixture()

    assert len(generated_list) == 2

    expected_code = """
@pytest.fixture
def generate_x(generate_y):
    x = y + 1
    return x
"""
    expected_ast = ast.parse(expected_code, mode="exec")
    assert ast_equal(generated_list[0], expected_ast)

    expected_code = """
@pytest.fixture
def generate_y():
    y = 42
    return y
"""
    expected_ast = ast.parse(expected_code, mode="exec")
    assert ast_equal(generated_list[1], expected_ast)

def test_make_fixture_3():
    dep_dep_body = [ast.parse("z = 42", mode="exec").body[0]]
    dep_dep_ret = ast.Return(value=ast.Name(id="z", ctx=ast.Load()))
    dep_dep = MetaFixture(depends=[], parameter="z", body=dep_dep_body, ret=dep_dep_ret)

    dep_body = [ast.parse("y = z + 1", mode="exec").body[0]]
    dep_ret = ast.Return(value=ast.Name(id="y", ctx=ast.Load()))
    dep = MetaFixture(depends=[dep_dep], parameter="y", body=dep_body, ret=dep_ret)

    body = [ast.parse("x = y + 1", mode="exec").body[0]]
    ret = ast.Return(value=ast.Name(id="x", ctx=ast.Load()))
    mf = MetaFixture(depends=[dep], parameter="x", body=body, ret=ret)

    generated_list = mf.make_fixture()

    assert len(generated_list) == 3

    expected_code = """
@pytest.fixture
def generate_x(generate_y):
    x = y + 1
    return x
"""
    expected_ast = ast.parse(expected_code, mode="exec")
    assert ast_equal(generated_list[0], expected_ast)

    expected_code = """
@pytest.fixture
def generate_y(generate_z):
    y = z + 1
    return y
"""
    expected_ast = ast.parse(expected_code, mode="exec")
    assert ast_equal(generated_list[1], expected_ast)

    expected_code = """
@pytest.fixture
def generate_z():
    z = 42
    return z
"""
    expected_ast = ast.parse(expected_code, mode="exec")
    assert ast_equal(generated_list[2], expected_ast)

def test_make_fixture_4():
    dep_1_body = [ast.parse("z = 42", mode="exec").body[0]]
    dep_1_ret = ast.Return(value=ast.Name(id="z", ctx=ast.Load()))
    dep_1 = MetaFixture(depends=[], parameter="z", body=dep_1_body, ret=dep_1_ret)

    dep_2_body = [ast.parse("foo = Foo()", mode="exec").body[0]]
    dep_2_ret = ast.Return(value=ast.Name(id="foo", ctx=ast.Load()))
    dep_2 = MetaFixture(depends=[], parameter="foo", body=dep_2_body, ret=dep_2_ret)

    body = [ast.parse("x = foo(z)", mode="exec").body[0]]
    ret = ast.Return(value=ast.Name(id="x", ctx=ast.Load()))
    mf = MetaFixture(depends=[dep_1, dep_2], parameter="x", body=body, ret=ret)

    generated_list = mf.make_fixture()

    assert len(generated_list) == 3

    expected_code = """
@pytest.fixture
def generate_x(generate_z, generate_foo):
    x = foo(z)
    return x
"""
    expected_ast = ast.parse(expected_code, mode="exec")
    assert ast_equal(generated_list[0], expected_ast)

    expected_code = """
@pytest.fixture
def generate_z():
    z = 42
    return z
"""
    expected_ast = ast.parse(expected_code, mode="exec")
    assert ast_equal(generated_list[1], expected_ast)

    expected_code = """
@pytest.fixture
def generate_foo():
    foo = Foo()
    return foo
"""
    expected_ast = ast.parse(expected_code, mode="exec")
    assert ast_equal(generated_list[2], expected_ast)


def test_make_fixture_no_dependencies():
    """Test creating a fixture without dependencies."""
    body = [ast.parse("value = 100", mode="exec").body[0]]
    ret = ast.Return(value=ast.Name(id="value", ctx=ast.Load()))
    mf = MetaFixture(depends=[], parameter="value", body=body, ret=ret)

    generated_list = mf.make_fixture()

    assert len(generated_list) == 1
    fixture = generated_list[0]
    assert isinstance(fixture, ast.FunctionDef)
    assert fixture.name == "generate_value"
    assert len(fixture.args.args) == 0  # No dependencies
    assert len(fixture.body) == 2  # body statement + return


def test_make_fixture_diamond_dependency():
    """Test creating a fixture with diamond dependency pattern."""
    # Create base fixture (bottom of diamond)
    base_body = [ast.parse("base = 1", mode="exec").body[0]]
    base_ret = ast.Return(value=ast.Name(id="base", ctx=ast.Load()))
    base = MetaFixture(depends=[], parameter="base", body=base_body, ret=base_ret)

    # Create two middle fixtures that depend on base
    left_body = [ast.parse("left = base * 2", mode="exec").body[0]]
    left_ret = ast.Return(value=ast.Name(id="left", ctx=ast.Load()))
    left = MetaFixture(depends=[base], parameter="left", body=left_body, ret=left_ret)

    right_body = [ast.parse("right = base * 3", mode="exec").body[0]]
    right_ret = ast.Return(value=ast.Name(id="right", ctx=ast.Load()))
    right = MetaFixture(depends=[base], parameter="right", body=right_body, ret=right_ret)

    # Create top fixture that depends on both left and right
    top_body = [ast.parse("top = left + right", mode="exec").body[0]]
    top_ret = ast.Return(value=ast.Name(id="top", ctx=ast.Load()))
    top = MetaFixture(depends=[left, right], parameter="top", body=top_body, ret=top_ret)

    generated_list = top.make_fixture()

    # Should have 4 fixtures: top, left, right, base (but base should appear only once)
    assert len(generated_list) == 4

    # Check top fixture has correct name and dependencies
    top_fixture = generated_list[0]
    assert isinstance(top_fixture, ast.FunctionDef)
    assert top_fixture.name == "generate_top"
    assert len(top_fixture.args.args) == 2  # depends on left and right
    param_names = [arg.arg for arg in top_fixture.args.args]
    assert "generate_left" in param_names
    assert "generate_right" in param_names


def test_make_fixture_with_complex_body():
    """Test creating a fixture with multiple statements in body."""
    body = [
        ast.parse("temp = 10", mode="exec").body[0],
        ast.parse("result = temp * 2", mode="exec").body[0],
        ast.parse("result += 5", mode="exec").body[0],
    ]
    ret = ast.Return(value=ast.Name(id="result", ctx=ast.Load()))
    mf = MetaFixture(depends=[], parameter="result", body=body, ret=ret)

    generated_list = mf.make_fixture()

    assert len(generated_list) == 1
    fixture = generated_list[0]
    assert isinstance(fixture, ast.FunctionDef)
    assert fixture.name == "generate_result"
    assert len(fixture.body) == 4  # 3 body statements + return


def test_make_fixture_three_linear_dependencies():
    """Test creating a fixture with three linear dependencies."""
    # dep1 depends on nothing
    dep1_body = [ast.parse("a = 5", mode="exec").body[0]]
    dep1_ret = ast.Return(value=ast.Name(id="a", ctx=ast.Load()))
    dep1 = MetaFixture(depends=[], parameter="a", body=dep1_body, ret=dep1_ret)

    # dep2 depends on dep1
    dep2_body = [ast.parse("b = a * 2", mode="exec").body[0]]
    dep2_ret = ast.Return(value=ast.Name(id="b", ctx=ast.Load()))
    dep2 = MetaFixture(depends=[dep1], parameter="b", body=dep2_body, ret=dep2_ret)

    # dep3 depends on dep2
    dep3_body = [ast.parse("c = b + 10", mode="exec").body[0]]
    dep3_ret = ast.Return(value=ast.Name(id="c", ctx=ast.Load()))
    dep3 = MetaFixture(depends=[dep2], parameter="c", body=dep3_body, ret=dep3_ret)

    # main depends on dep3
    main_body = [ast.parse("result = c * 3", mode="exec").body[0]]
    main_ret = ast.Return(value=ast.Name(id="result", ctx=ast.Load()))
    main = MetaFixture(depends=[dep3], parameter="result", body=main_body, ret=main_ret)

    generated_list = main.make_fixture()

    assert len(generated_list) == 4

    # Check main fixture
    result_fixture = generated_list[0]
    assert isinstance(result_fixture, ast.FunctionDef)
    assert result_fixture.name == "generate_result"
    assert len(result_fixture.args.args) == 1  # depends on c
    assert result_fixture.args.args[0].arg == "generate_c"


