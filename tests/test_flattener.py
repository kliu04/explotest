import ast

import pytest

from explotest.tracer import ASTFlattener


@pytest.fixture
def setup_example():
    def _load_ast(name: str):
        with open(f"./data/{name}.py") as f:
            return ast.parse(f.read())

    return _load_ast


@pytest.mark.parametrize("example_name", ["ex3", "ex4"])
def test_flattener(example_name, setup_example):
    flattener = ASTFlattener()
    new_statements = []
    for stmt in setup_example(example_name).body:
        new_statements.extend(flattener.flatten(stmt))
    result = ast.Module(body=new_statements, type_ignores=[])

    assert ast.dump(result) == ast.dump(setup_example(f"{example_name}r"))
