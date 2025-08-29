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



