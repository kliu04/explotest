import ast

import pytest

from explotest.tracer import ASTRewriter, TrackedFile


@pytest.fixture
def setup_example():
    def _load_ast(name: str):
        with open(f"./data/{name}.py") as f:
            return ast.parse(f.read())

    return _load_ast


@pytest.mark.parametrize("example_name", ["ex3", "ex4", "ex5a"])
def test_rewriter(example_name, setup_example):
    rewriter = ASTRewriter(TrackedFile(setup_example(example_name)))
    result = rewriter.rewrite()
    assert ast.dump(result) == ast.dump(setup_example(f"{example_name}r"))
