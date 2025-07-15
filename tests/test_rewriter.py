import ast

import pytest

from explotest.ast_file import ASTFile
from explotest.ast_rewriter import ASTRewriter


@pytest.fixture
def setup_example():
    def _load_ast(name: str):
        with open(f"./data/{name}.py") as f:
            return ast.parse(f.read())

    return _load_ast


n = 4


@pytest.mark.parametrize("example_name", [f"rewriter_test_{i}" for i in range(1, n)])
def test_rewriter(example_name, setup_example):
    rewriter = ASTRewriter(ASTFile(setup_example(example_name)))
    result = rewriter.rewrite()
    assert ast.dump(result) == ast.dump(setup_example(f"{example_name}_expected"))
