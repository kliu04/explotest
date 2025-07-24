"""
The global state detector detects all potential global state in a program. For now, the strategy is static in nature.
It's a part of the test generation pass cycle. All global state will probably be mocked.
"""

import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, override, Generator, Literal

from numpy.f2py.auxfuncs import isintent_in

from src.explotest.reconstructor import Reconstructor


@dataclass
class External(ABC):
    value: Any

    @abstractmethod
    def get_mock(self, reconstructor: Reconstructor) -> list[ast.AST]: ...


@dataclass
class NamedExternal(External, ABC):
    name: str


@dataclass
class ExternalVariable(NamedExternal):
    @override
    def get_mock(self, reconstructor: Reconstructor) -> list[ast.AST]:
        return []  # stub


@dataclass
class ExternalProcedure(NamedExternal):
    @override
    def get_mock(self, reconstructor: Reconstructor) -> list[ast.AST]:
        return []  # stub


@dataclass
class CallToOpen(External):
    @override
    def get_mock(self, reconstructor: Reconstructor) -> list[ast.AST]:
        return []  # stub


def find_global_vars(source: ast.Module, proc_name: str) -> list[External]:
    """
    Returns the fully qualified names of all the global variables used in a specified function.
    Raises `ValueError` if function was not found in the source.
    """

    result = []

    target_def = find_function_def(source, proc_name)

    if target_def is None:
        raise ValueError(
            f"Function definition not found! source:\n{ast.dump(source, indent=4)}\n\nproc_name: {proc_name}"
        )

    args = target_def.args

    for idx, line in enumerate(target_def.body):
        # print("proc: find_global_vars")
        # print(ast.unparse(line))
        # print("end proc")
        named_attrs = find_names_attributes(line)
        for attr in named_attrs:
            print(attr)
            attribute_parent = unwrap_attribute(attr)
            if attribute_parent == "CONSTANT":
                continue  # ignore this one, as it's an operation on a constant. string functions are immutable
            defn = find_var_defn(attribute_parent, idx, target_def)
            if defn is None and ast.unparse(
                ast.fix_missing_locations(attribute_parent)
            ) not in [a.arg for a in args.args]:
                result.append(attr)

    return result


def unwrap_attribute(
    attribute: ast.Attribute | ast.Name,
) -> ast.Name | Literal["CONSTANT"]:
    if isinstance(
        attribute, ast.Constant
    ):  # case where parent is an instance literal, e.g., a string "abc"
        return "CONSTANT"

    if isinstance(attribute, ast.Name):
        return attribute
    parent = attribute.value

    return unwrap_attribute(parent)


def find_names_attributes(line: ast.AST) -> list[ast.Attribute | ast.Name]:
    """
    Returns all the names and attribute access on a line
    """
    result: list[ast.Attribute | ast.Name] = []

    class AttributeAndNameVisitor(ast.NodeVisitor):
        def visit_Attribute(self, node: ast.Attribute):
            result.append(node)

        def visit_Name(self, node: ast.Name):
            result.append(node)

    if isinstance(line, ast.Attribute) or isinstance(line, ast.Name):
        return [line]

    v = AttributeAndNameVisitor()
    v.visit(line)

    return result


def find_var_defn(
    var: ast.Name, var_idx_in_body: int, func: ast.FunctionDef
) -> ast.Assign | None:
    """
    Find the variable definition of the variable passed in w/ a functiondef.
    Returns none if no in-function definition was found.
    """
    lines_to_look_at = func.body[0:var_idx_in_body]
    for line in reversed(lines_to_look_at):  # look bottom up
        # find any assigns to var
        if isinstance(line, ast.Assign):
            if any(
                [
                    ast.unparse(ast.fix_missing_locations(target))
                    == ast.unparse(ast.fix_missing_locations(var))
                    for target in line.targets
                    if isinstance(target, ast.Name)
                ]
            ):
                return line
    return None


def find_function_def(source: ast.Module, proc_name: str) -> ast.FunctionDef | None:
    """
    Finds the function definition with `proc_name`. Returns None if not found.
    TODO: support function overloading.
    """
    for line in source.body:
        if isinstance(line, ast.FunctionDef):
            if proc_name == line.name:
                return line
    return None
