import ast
import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar, cast

from .helpers import is_primitive, is_collection, random_id
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
        # corresponds to: setattr(x, attribute_name, generate_attribute_value)
        # or falls back to pickling
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
        return not inspect.isfunction(obj) and not inspect.ismethod(obj)

    def _reconstruct_collection(self, parameter, collection) -> PyTestFixture:
        # primitive values in collections will remain as is
        # E.g., [1, 2, <Object1>, <Object2>] -> [1, 2, generate_object1_type_id, generate_object2_type_id]
        # where id is an 8 digit random hex code

        deps = []
        ptf_body = []

        def generate_elt_name(t: str) -> str:
            return f"{t}_{random_id()}"

        def elt_to_ast(obj):
            if is_primitive(obj):
                return ast.Constant(value=obj)
            else:
                rename = generate_elt_name(obj.__class__.__name__)
                deps.append(self._ast(rename, obj))
                return ast.Name(id=f"generate_{rename}", ctx=ast.Load())

        if isinstance(collection, dict):
            d = {
                elt_to_ast(key): elt_to_ast(value) for key, value in collection.items()
            }

            _clone = cast(
                ast.AST,
                ast.Assign(
                    targets=[ast.Name(id=parameter, ctx=ast.Store())],
                    value=ast.Dict(
                        keys=list(d.keys()),
                        values=list(d.values()),
                    ),
                ),
            )
        else:
            collection_ast_type: Any
            if isinstance(collection, list):
                collection_ast_type = ast.List
            elif isinstance(collection, tuple):
                collection_ast_type = ast.Tuple
            elif isinstance(collection, set):
                collection_ast_type = ast.Set
            else:
                assert False  # unreachable

            collection_asts = list(map(elt_to_ast, collection))

            _clone = cast(
                ast.AST,
                ast.Assign(
                    targets=[ast.Name(id=parameter, ctx=ast.Store())],
                    value=collection_ast_type(
                        elts=collection_asts,
                        ctx=ast.Load(),
                    ),
                ),
            )
        _clone = ast.fix_missing_locations(_clone)
        ptf_body.append(_clone)

        # Return the clone
        ret = ast.fix_missing_locations(
            ast.Return(value=ast.Name(id=f"clone_{parameter}", ctx=ast.Load()))
        )
        return PyTestFixture(deps, parameter, ptf_body, ret)

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
            return self._reconstruct_collection(parameter, obj)

        module_path: str | None = inspect.getfile(type(obj))

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
                _setattr = ast.Expr(
                    value=ast.Call(
                        func=ast.Name(id="setattr", ctx=ast.Load()),
                        args=[
                            ast.Name(id=clone_name, ctx=ast.Load()),
                            ast.Name(id=f"'{attribute_name}'", ctx=ast.Load()),
                            ast.Constant(value=attribute_value),
                        ],
                    )
                )
            else:
                uniquified_name = (
                    f"{parameter}_{attribute_name}"  # needed to avoid name collisions
                )
                deps.append(self._ast(uniquified_name, attribute_value))
                _setattr = ast.Expr(
                    value=ast.Call(
                        func=ast.Name(id="setattr", ctx=ast.Load()),
                        args=[
                            ast.Name(id=clone_name, ctx=ast.Load()),
                            ast.Name(id=f"'{attribute_name}'", ctx=ast.Load()),
                            ast.Name(id=f"generate_{uniquified_name}", ctx=ast.Load()),
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
