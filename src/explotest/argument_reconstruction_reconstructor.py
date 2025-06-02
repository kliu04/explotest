import ast
import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.explotest.helpers import is_primitive
from src.explotest.pickle_reconstructor import PickleReconstructor
from src.explotest.pytest_fixture import PyTestFixture
from src.explotest.reconstructor import Reconstructor


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
        # TODO: this does not work
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
        # create an instance without calling __init__
        # E.g., clone = foo.Foo.__new__(foo.Foo) (for file foo.py that defines a class Foo)

        clone_name = f"clone_{parameter}"
        module_path: str | None = inspect.getsourcefile(type(obj))
        if module_path is None:
            raise Exception(f"module at {module_path} not found.")

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
        deps = []
        for attribute_name, attribute_value in attributes:
            if is_primitive(attribute_value):
                # corresponds to: setattr(x, attribute_name, attribute_value)
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
                _setattr = ast.fix_missing_locations(_setattr)
                ptf_body.append(_setattr)
                continue
            elif ArgumentReconstructionReconstructor.is_class_instance(attribute_value):
                # corresponds to: setattr(x, attribute_name, generate_attribute_name)
                deps.append(
                    self._reconstruct_object_instance(attribute_name, attribute_value)
                )
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
