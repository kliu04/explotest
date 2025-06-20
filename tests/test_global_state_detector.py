import ast
from ast import *
from pathlib import Path

import pytest

from src.explotest.global_state_detector import (
    find_global_vars,
    External,
    ExternalVariable,
    CallToOpen,
    ExternalProcedure,
    find_names_attributes,
    find_function_def,
    find_var_defn,
)

# --- possible global state exposers:

src1_expected = [
    ExternalVariable(
        value=["hello", "world"],
        name="test_data.test_global_state_detector.source1.lst",
    )
]

src2_expected = [CallToOpen(value="meowmeow2")]

src3_expected = [
    ExternalProcedure(value=None, name="flask.globals.request.args.target()"),
    ExternalProcedure(
        value=None, name=r"todoism.modelItem.query.with_parent().filter_by().paginate()"
    ),
    ExternalProcedure(name="flask.helpers.url_for()", value=None),
    ExternalProcedure(name="flask.helpers.url_for()", value=None),
    ExternalProcedure(name="flask.helpers.url_for()", value=None),
]


@pytest.mark.parametrize(
    "source,expected",
    [
        (ast.parse(src.read_text()), expected)
        for src, expected in zip(
            Path("../test_data/test_global_state_detector").glob("**.py"),
            [src1_expected, src2_expected, src3_expected],
        )
    ],
)
class TestFindGlobalVars:
    def test_find_global_vars(self, source: ast.Module, expected: list[External]):
        result = find_global_vars(source, "target")
        assert expected == result


def test_find_names_attributes():
    target_func = parse(
        """
def foo():
    x.y.z = 3
    f = 3
"""
    )
    assert [
        unparse(a)
        for a in [
            Attribute(
                value=Attribute(value=Name(id="x", ctx=Load()), attr="y", ctx=Load()),
                attr="z",
                ctx=Store(),
            ),
            Name(id="f", ctx=Store()),
        ]
    ] == [
        unparse(a)
        for a in [
            find_names_attributes(l) for l in find_function_def(target_func, "foo").body
        ]
    ]


def test_find_var_defn():
    # noinspection PyTypeChecker
    target_func: ast.FunctionDef = parse(  # pyright: ignore [reportAssignmentType]
        """
def foo():
    x = 3
    x.y()
        """
    ).body[0]
    expected_defn = fix_missing_locations(
        Assign(targets=[Name(id="x", ctx=Store())], value=Constant(value=3))
    )
    call: ast.Call = target_func.body[1].value  # pyright: ignore [reportAssignmentType]
    assert isinstance(call, ast.Call)

    assert unparse(expected_defn) == unparse(
        find_var_defn(call.func.value, 1, target_func)
    )
