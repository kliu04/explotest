import ast
import inspect
from collections import deque
from typing import override, Any, Optional, cast

from ..helpers import is_primitive, collection_t, random_id, is_collection
from ..meta_fixture import MetaFixture
from ..reconstructors.abstract_reconstructor import AbstractReconstructor


class LazyProxy:
    def __init__(self):
        self._real = None

    def set_real(self, obj):
        self._real = obj

    def __getattr__(self, name):
        return getattr(self._real, name)


def get_next_attrs(o: Any) -> list[Any]:
    """
    Returns all the data-only attributes of the current node.
    """
    # need to use the type of the current object to avoid triggering properties
    cls = o.__class__
    return [
        n
        for n, v in inspect.getmembers(cls)
        if not inspect.isroutine(v)
        and not n.startswith("__")
        and not isinstance(v, property)
    ]


class ArgumentReconstructor(AbstractReconstructor):

    @override
    def make_fixture(self, parameter, argument):
        return self._make_fixture(parameter, argument, [])

    def _make_fixture(self, parameter, argument, seen_args: list[tuple[Any, Any]]):
        """
        :param parameter: The parameter (as a string) to create the MetaFixture for
        :param argument: Runtime value of the argument
        :param seen_args: Keeps track of seen arguments to avoid cycles
        :return: The MetaFixture needed to recreate the argument, or None if ExploTest fails.
        """

        if is_primitive(argument):
            return super()._make_primitive_fixture(parameter, argument)

        # argument exists in mapping
        for k, v in seen_args:
            if k == argument:
                return v

        if self.is_reconstructible(argument):
            placeholder = LazyProxy()
            seen_args.append((argument, placeholder))
            reconstructed = self._reconstruct_object_instance(
                parameter, argument, seen_args
            )
            placeholder.set_real(reconstructed)
            return reconstructed

        if self.backup_reconstructor:
            placeholder = LazyProxy()
            seen_args.append((argument, placeholder))
            reconstructed = self.backup_reconstructor.make_fixture(parameter, argument)
            placeholder.set_real(reconstructed)
            return reconstructed

        return None

    def _reconstruct_collection(
        self, parameter: str, collection: collection_t, seen_args
    ) -> Optional[MetaFixture]:
        """
        Given a parameter and a collection, attempt to recreate the collection.
        :param parameter:
        :param collection:
        :return:
        """
        # primitive values in collections will remain as is
        # E.g., [1, 2, <Object1>, <Object2>] -> [1, 2, generate_object1_type_id, generate_object2_type_id]
        # where id is an 8 digit random hex code

        deps = []
        meta_fixture_body = []

        def generate_elt_name(t: str) -> str:
            return f"{t}_{random_id()}"

        def elt_to_ast(obj) -> Optional[ast.AST]:
            if is_primitive(obj):
                return ast.Constant(value=obj)
            else:
                rename = generate_elt_name(obj.__class__.__name__)
                new_fixture = self._make_fixture(rename, obj, seen_args)
                if new_fixture is None:
                    return None
                deps.append(new_fixture)
                return ast.Name(id=f"generate_{rename}", ctx=ast.Load())

        if isinstance(collection, dict):
            d = {
                elt_to_ast(key): elt_to_ast(value) for key, value in collection.items()
            }

            if any(v is None for v in d.values()):
                return None

            assert all(v is not None for v in d.values())

            _clone = cast(
                ast.AST,
                ast.Assign(
                    targets=[ast.Name(id=f"clone_{parameter}", ctx=ast.Store())],
                    value=ast.Dict(
                        keys=cast(list[Optional[ast.expr]], list(d.keys())),
                        values=list(d.values()),  # type: ignore
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
            if any(v is None for v in collection_asts):
                return None

            assert all(v is not None for v in collection_asts)

            _clone = cast(
                ast.AST,
                ast.Assign(
                    targets=[ast.Name(id=f"clone_{parameter}", ctx=ast.Store())],
                    value=collection_ast_type(  # type: ignore
                        elts=collection_asts,
                        ctx=ast.Load(),
                    ),
                ),
            )
        _clone = ast.fix_missing_locations(_clone)
        meta_fixture_body.append(_clone)

        # Return the clone
        ret = ast.fix_missing_locations(
            ast.Return(value=ast.Name(id=f"clone_{parameter}", ctx=ast.Load()))
        )
        return MetaFixture(deps, parameter, meta_fixture_body, ret)

    def _reconstruct_object_instance(
        self, parameter: str, obj: Any, seen_args
    ) -> Optional[MetaFixture]:
        """Return an MetaFixture representation of a clone of obj by setting attributes equal to obj."""

        # taken from inspect.getmembers(Foo()) on empty class Foo
        builtins = [
            "__dict__",
            "__doc__",
            "__firstlineno__",
            "__module__",
            "__static_attributes__",
            "__weakref__",
        ]

        cls = obj.__class__
        attributes = get_next_attrs(cls)

        ptf_body: list[ast.AST] = []
        deps: list[MetaFixture] = []

        # create an instance without calling __init__
        # E.g., clone = foo.Foo.__new__(foo.Foo) (for file foo.py that defines a class Foo)

        clone_name = f"clone_{parameter}"

        if is_collection(obj):
            return self._reconstruct_collection(parameter, obj, seen_args)

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
                new_fixture = self._make_fixture(
                    uniquified_name, attribute_value, seen_args
                )
                if new_fixture is None:
                    return None
                deps.append(new_fixture)
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
        return MetaFixture(deps, parameter, cast(list[ast.stmt], ptf_body), ret)

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
                # "isproperty": isinstance(o, property)
            }
            return any(results.values())

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
                # primitives are trivially reconstructible
                if not in_that_uses_is(next_attr, visited) and not is_primitive(
                    next_attr
                ):
                    visited.append(next_attr)
                    if is_bad(next_attr):
                        is_bad(next_attr)
                        return False
                    q.append(next_attr)
        return True
