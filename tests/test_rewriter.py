import ast

import pytest

from explotest.tracer import TFRewriter, TrackedFile


@pytest.fixture
def setup_example():
    def _load_ast(name: str):
        with open(f"./data/{name}.py") as f:
            return ast.parse(f.read())

    return _load_ast


@pytest.mark.parametrize("example_name", ["ex3", "ex4", "ex5a", "ex6"])
def test_rewriter(example_name, setup_example):
    rewriter = TFRewriter(TrackedFile(setup_example(example_name)))
    result = rewriter.rewrite()
    print(ast.unparse(result))
    assert ast.dump(result) == ast.dump(setup_example(f"{example_name}r"))

@pytest.mark.parametrize(
    "example_name, lines, cln",
    [
        ("ex6", {1, 2, 3, 4, 10, 12, 13, 14, 16, 17, 19, 20, 22, 23, 24, 26, 27},
            [1, 2, 3, 4, 8, 9, 10, 11, 15, 16, 18, 19, 24, 27, 30, 31, 33])
    ],
)
def test_rewriter_linenos(example_name, lines, cln, setup_example):
    file = TrackedFile(setup_example(example_name))
    file.abstract_line_numbers = lines
    rewriter = TFRewriter(file)
    result = rewriter.rewrite()
    assert ast.dump(result) == ast.dump(setup_example(f"{example_name}r"))
    # assert file.concrete_line_numbers == cln