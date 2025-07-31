import ast
import random
import uuid
from pathlib import Path

import pytest

from explotest.ast_file import ASTFile
from explotest.ast_rewriter import ASTRewriterA, ASTRewriterB


@pytest.fixture
def setup_example():
    def _load_ast(name: str):
        with open(f"./data/{name}.py") as f:
            return ast.parse(f.read())

    return _load_ast


DIR = "./data"
pathlist = Path(DIR).glob(f"*rewriter_a_input*.py")
n = len(list(pathlist)) + 1


@pytest.mark.parametrize("example_name", [f"rewriter_a_input_{i}" for i in range(1, n)])
def test_rewriter_a(example_name, setup_example):
    ast_file = ASTFile(example_name, setup_example(example_name))
    ast_file.transform(ASTRewriterA())
    expected_name = example_name.replace("input", "expected")
    assert ast.dump(ast_file.node) == ast.dump(setup_example(expected_name))


pathlist = Path(DIR).glob(f"*rewriter_b_input*.py")
n = len(list(pathlist)) + 1


@pytest.fixture
def fake_uuid():
    # make UUID deterministic
    rand = random.Random(0)

    def _fake_uuid():
        return uuid.UUID(int=rand.getrandbits(128))

    return _fake_uuid


@pytest.mark.parametrize("example_name", [f"rewriter_b_input_{i}" for i in range(1, n)])
def test_rewriter_b(example_name, setup_example, monkeypatch, fake_uuid):
    monkeypatch.setattr(uuid, "uuid4", fake_uuid)
    ast_file = ASTFile(example_name, setup_example(example_name))
    ast_file.transform(ASTRewriterB())
    expected_name = example_name.replace("input", "expected")
    assert ast.dump(ast_file.node) == ast.dump(setup_example(expected_name))
