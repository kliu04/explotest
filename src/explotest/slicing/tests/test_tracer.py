import ast

from pytest import fixture

from explotest.slicing.explotest import ASTTracer, TrackedFile


@fixture
def setup_example():
    def _load_ast(name: str):
        with open(f"files/{name}.py") as f:
            return ast.parse(f.read())

    return _load_ast


def test_tracer_1(setup_example):
    file = TrackedFile(setup_example("ex1"), {4, 5, 6, 7, 13})
    tracer = ASTTracer()
    tracer.tracked_file = file
    result = tracer.visit(file.nodes)
    with open("files/ex1r.py") as f:
        return result == f.read()


def test_tracer_2(setup_example):
    file = TrackedFile(setup_example("ex2"), {1, 2, 3, 4, 5, 7, 15, 24, 27})
    tracer = ASTTracer()
    tracer.tracked_file = file
    result = tracer.visit(file.nodes)
    with open("files/ex2r.py") as f:
        return result == f.read()
