import ast

import pytest

from explotest.__main__ import TFPruner, TrackedFile


@pytest.fixture
def setup_example():
    def _load_ast(name: str):
        with open(f"./data/{name}.py") as f:
            return ast.parse(f.read())

    return _load_ast


@pytest.mark.parametrize(
    "example_name, lines",
    [
        ("ex1", {4, 5, 6, 7, 13}),
        ("ex2", {1, 2, 3, 4, 5, 7, 15, 24, 27}),
        ("ex5b", {1, 2, 3, 4, 5, 7}),
    ],
)
def test_tracer(example_name, lines, setup_example):
    file = TrackedFile(setup_example(example_name))
    file.traced_line_numbers = lines
    tracer = TFPruner(file)
    result = tracer.visit(file.nodes)
    assert ast.dump(result) == ast.dump(setup_example(f"{example_name}r"))
