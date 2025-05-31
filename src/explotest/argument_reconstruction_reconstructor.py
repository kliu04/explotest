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
        """Return an PTF representation of a clone of obj by setting attributes equal to obj"""

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

        ptf = PyTestFixture([], parameter, [])

        # create an instance without calling __init__
        # E.g., clone = Foo.__new__(Foo)
        clone_name = f"clone_{parameter}"
        _clone = ast.Assign(
            targets=[ast.Name(id=clone_name, ctx=ast.Store())],
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id=type(obj).__name__, ctx=ast.Load()),
                    attr="__new__",
                    ctx=ast.Load(),
                ),
                args=[ast.Name(id=type(obj).__name__, ctx=ast.Load())],
            ),
        )
        _clone = ast.fix_missing_locations(_clone)
        ptf.body.append(_clone)

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
                ptf.body.append(_setattr)
                continue

            elif ArgumentReconstructionReconstructor.is_class_instance(attribute_value):
                # corresponds to: setattr(x, attribute_name, generate_attribute_name)

                # TODO: need to add a return statement here
                ptf.depends.append(
                    self._reconstruct_object_instance(attribute_name, attribute_value)
                )

            else:
                # if unsettable, should fallback on pickling
                ptf.depends.append(
                    self.backup_reconstructor._ast(attribute_name, attribute_value)
                )

            _setattr = ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="setattr", ctx=ast.Load()),
                    args=[
                        ast.Name(id=clone_name, ctx=ast.Load()),
                        ast.Name(id=attribute_name, ctx=ast.Load()),
                        ast.Name(id=f"generate_{attribute_name}", ctx=ast.Load()),
                    ],
                )
            )
            _setattr = ast.fix_missing_locations(_setattr)
            ptf.body.append(_setattr)

        return ptf
