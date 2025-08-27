import ast
import inspect
from collections import deque
from dataclasses import dataclass, field
from typing import Any, cast

from .abstract_fixture import AbstractFixture
from .helpers import is_primitive, is_collection, random_id
from .reconstructor import Reconstructor


@dataclass
class ArgumentReconstructor(Reconstructor):

    seen: list[str] = field(default_factory=list)

    def _ast(self, parameter, argument):
        # corresponds to: setattr(x, attribute_name, generate_attribute_value)
        # or falls back to pickling
        if is_primitive(argument):
            return Reconstructor._reconstruct_primitive(parameter, argument)
        elif ArgumentReconstructor.is_reconstructible(argument):
            return self._reconstruct_object_instance(parameter, argument)
        else:
            backup = self.backup_reconstructor(self.file_path)
            return backup._ast(parameter, argument)

    @staticmethod
    def is_reconstructible(obj: Any) -> bool:
        """True iff object is an instance of a user-defined class."""

        def is_bad(o: Any) -> bool:
            results = {
                "ismodule": inspect.ismodule(o),
                "isclass": inspect.isclass(o),
                "ismethod": inspect.ismethod(o),
                "isfunction": inspect.isfunction(o),
                "isgenerator": inspect.isgenerator(o),
                "isgeneratorfunction": inspect.isgeneratorfunction(o),
                "iscoroutine": inspect.iscoroutine(o),
                "iscoroutinefunction": inspect.iscoroutinefunction(o),
                "isawaitable": inspect.isawaitable(o),
                "isasyncgen": inspect.isasyncgen(o),
                "istraceback": inspect.istraceback(o),
                "isframe": inspect.isframe(o),
                "isbuiltin": inspect.isbuiltin(o),
                "ismethodwrapper": inspect.ismethodwrapper(o),
                "isgetsetdescriptor": inspect.isgetsetdescriptor(o),
                "ismemberdescriptor": inspect.ismemberdescriptor(o),
            }
            return any(results.values())

        def get_next_attrs(o: Any) -> list[Any]:
            """
            Returns all the data-only attributes of the current node.
            """
            return [
                v
                for n, v in inspect.getmembers(o)
                if not inspect.isroutine(v) and not n.startswith("__")
            ]

        def in_that_uses_is(o: Any, lst: list[Any]):
            """
            We want to check reference equality for fields, not actual equality as they might have custom implementations
            of `__eq__`.
            """
            return any([o is i for i in lst])

        if is_bad(obj):
            return False

        visited: list[Any] = []

        q: deque[Any] = deque()
        q.append(obj)

        while len(q) != 0:
            current_obj = q.popleft()
            visited.append(current_obj)
            # no need to explore current node as we have already explored it with is_bad
            for next_attr in get_next_attrs(current_obj):
                # fixes infinite cycling due to int pooling w/ check to is_primitive
                # https://stackoverflow.com/questions/6101379/what-happens-behind-the-scenes-when-python-adds-small-ints
                # primitives are trivally reconstructible
                if not in_that_uses_is(next_attr, visited) and not is_primitive(
                    next_attr
                ):
                    visited.append(next_attr)
                    if is_bad(next_attr):
                        is_bad(next_attr)
                        return False
                    q.append(next_attr)
        return True

    def _reconstruct_collection(self, parameter, collection) -> AbstractFixture:
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
                    targets=[ast.Name(id=f"clone_{parameter}", ctx=ast.Store())],
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
                    targets=[ast.Name(id=f"clone_{parameter}", ctx=ast.Store())],
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
        return AbstractFixture(deps, parameter, ptf_body, ret)

    def _reconstruct_object_instance(self, parameter: str, obj: Any) -> AbstractFixture:
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
        # filter out properties
        # type(obj) is the class obj is defined from
        # x[0] is the name of the variable
        attributes = list(filter(lambda x : not isinstance(getattr(type(obj), x[0], None), property), attributes))
        
        ptf_body: list[ast.AST] = []
        print(attributes)
        deps: list[AbstractFixture] = []

        # create an instance without calling __init__
        # E.g., clone = foo.Foo.__new__(foo.Foo) (for file foo.py that defines a class Foo)

        clone_name = f"clone_{parameter}"

        if is_collection(obj):
            return self._reconstruct_collection(parameter, obj)

        module_name = self.file_path.stem

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
        return AbstractFixture(deps, parameter, ptf_body, ret)
