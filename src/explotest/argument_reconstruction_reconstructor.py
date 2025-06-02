import ast
import inspect
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from .helpers import is_primitive, is_collection
from .pickle_reconstructor import PickleReconstructor
from .pytest_fixture import PyTestFixture
from .reconstructor import Reconstructor

X = TypeVar("X")


@dataclass(frozen=True)
class ArgumentReconstructionReconstructor(Reconstructor):

    backup_reconstructor: PickleReconstructor

    def __init__(self, file_path: Path):
        # hacky way to get around frozen-ness
        object.__setattr__(self, "backup_reconstructor", PickleReconstructor(file_path))

    def _ast(self, parameter, argument):
        if is_primitive(argument):
            return Reconstructor._reconstruct_primitive(parameter, argument)
        elif ArgumentReconstructionReconstructor.is_class_instance(argument):
            return self._reconstruct_object_instance(parameter, argument)
        else:
            return self.backup_reconstructor._ast(parameter, argument)

    @staticmethod
    def is_class_instance(obj: Any) -> bool:
        """True iff object is an instance of a user-defined class."""
        # FIXME: this does not work
        return not inspect.isfunction(obj)

    def _reconstruct_object_instance(self, parameter: str, obj: Any) -> PyTestFixture:
        """Return an PTF representation of a clone of obj by setting attributes equal to obj."""

        # taken from inspect.getmembers(Foo()) on empty class Foo
        builtins = [
            "__dict__",
            "__doc__",
            "__firstlineno__",
            "__module__",
            "__static_attributes__",
            "__weakref__",
        ]

        attributes = inspect.getmembers(obj, predicate=lambda x: not callable(x))
        attributes = list(filter(lambda x: x[0] not in builtins, attributes))
        ptf_body: list[ast.AST] = []
        deps: list[PyTestFixture] = []

        # create an instance without calling __init__
        # E.g., clone = foo.Foo.__new__(foo.Foo) (for file foo.py that defines a class Foo)

        clone_name = f"clone_{parameter}"

        if is_collection(obj):

            if isinstance(obj, dict):
                raise NotImplementedError()

            unique_names = [f"test_{uuid.uuid4().hex[:8]}" for _ in range(len(obj))]
            for i in range(len(obj)):
                deps.append(self._ast(unique_names[i], obj[i]))

            collection_ast_type: Any
            if isinstance(obj, list):
                collection_ast_type = ast.List
            elif isinstance(obj, tuple):
                collection_ast_type = ast.Tuple
            elif isinstance(obj, set):
                collection_ast_type = ast.Set
            else:
                assert False  # unreachable

            _clone = ast.Assign(
                targets=[ast.Name(id=parameter, ctx=ast.Store())],
                value=collection_ast_type(
                    elts=[
                        ast.Name(id=unique_name, ctx=ast.Load())
                        for unique_name in unique_names
                    ],
                    ctx=ast.Load(),
                ),
            )
            _clone = ast.fix_missing_locations(_clone)
            ptf_body.append(_clone)
            # Return the clone
            ret = ast.fix_missing_locations(
                ast.Return(value=ast.Name(id=f"clone_{parameter}", ctx=ast.Load()))
            )
            return PyTestFixture(deps, parameter, ptf_body, ret)

        module_path: str | None = inspect.getfile(type(obj))
        # FIXME: think about lists!!!!

        module_path: Path = Path(module_path)  # type: ignore
        module_name = module_path.stem  # type: ignore

        class_name = obj.__class__.__name__
        # Build ast for: module_name.class_name.__new__(module_name.class_name)
        qualified_class = ast.Attribute(
            value=ast.Name(id=module_name, ctx=ast.Load()),
            attr=class_name,
            ctx=ast.Load(),
        )
        _clone = ast.Assign(
            targets=[ast.Name(id=clone_name, ctx=ast.Store())],
            value=ast.Call(
                func=ast.Attribute(
                    value=qualified_class,
                    attr="__new__",
                    ctx=ast.Load(),
                ),
                args=[qualified_class],
            ),
        )
        _clone = ast.fix_missing_locations(_clone)
        ptf_body.append(_clone)
        for attribute_name, attribute_value in attributes:
            if is_primitive(attribute_value):
                deps.append(self._ast(attribute_name, attribute_value))
                # corresponds to: setattr(x, attribute_name, attribute_value)
            elif ArgumentReconstructionReconstructor.is_class_instance(attribute_value):
                # corresponds to: setattr(x, attribute_name, generate_attribute_name)
                deps.append(self._ast(attribute_name, attribute_value))
            else:
                # if unsettable, should fall back on pickling
                deps.append(
                    self.backup_reconstructor._ast(attribute_name, attribute_value)
                )
            _setattr = ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="setattr", ctx=ast.Load()),
                    args=[
                        ast.Name(id=clone_name, ctx=ast.Load()),
                        ast.Name(id=f"'{attribute_name}'", ctx=ast.Load()),
                        ast.Name(id=f"generate_{attribute_name}", ctx=ast.Load()),
                    ],
                )
            )
            _setattr = ast.fix_missing_locations(_setattr)
            ptf_body.append(_setattr)
        # Return the clone
        ret = ast.fix_missing_locations(
            ast.Return(value=ast.Name(id=f"clone_{parameter}", ctx=ast.Load()))
        )
        return PyTestFixture(deps, parameter, ptf_body, ret)
