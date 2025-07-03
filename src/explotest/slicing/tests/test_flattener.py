import ast

from pytest import fixture

from explotest.slicing.explotest import ASTFlattener


@fixture
def setup_example():
    def _load_ast(name: str):
        with open(f"files/{name}.py") as f:
            return ast.parse(f.read())

    return _load_ast


def test_flattener_1(setup_example):
    flattener = ASTFlattener()
    new_statements = []
    for stmt in setup_example("ex3").body:
        new_statements.extend(flattener.flatten(stmt))
    result = ast.Module(body=new_statements, type_ignores=[])
    with open("files/ex3r.py") as f:
        assert ast.dump(result) == ast.dump(ast.parse(f.read()))


def test_flattener_2(setup_example):
    flattener = ASTFlattener()
    new_statements = []
    for stmt in setup_example("ex4").body:
        new_statements.extend(flattener.flatten(stmt))
    result = ast.Module(body=new_statements, type_ignores=[])
    with open("files/ex4r.py") as f:
        assert ast.dump(result) == ast.dump(ast.parse(f.read()))
