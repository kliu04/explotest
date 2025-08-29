import ast
from typing import override, cast

import dill

from explotest.helpers import is_primitive, random_id
from explotest.meta_fixture import MetaFixture
from explotest.reconstructors.abstract_reconstructor import AbstractReconstructor


class PickleReconstructor(AbstractReconstructor):
    @override
    def make_fixture(self, parameter, argument) :
        if is_primitive(argument):
            return [super()._make_primitive_fixture(parameter, argument)]

        # create a unique ID for the pickled object
        pickled_id = random_id()

        # write the pickled object to file
        pickled_path = f"{self.file_path.parent}/pickled/{parameter}_{pickled_id}.pkl"
        try:
            with open(pickled_path, "wb") as f:
                f.write(dill.dumps(argument))
        except TypeError:
            print(f"[ERROR]: Unpickleable argument -- {type(argument)}")
            return None
        
        # create the fixture to generate the parameter
        generated_ast = cast(
            ast.AST,
            # corresponds to with open(pickled_path, "rb") as f:
            ast.With(
                items=[
                    ast.withitem(
                        context_expr=ast.Call(
                            func=ast.Name(id="open", ctx=ast.Load()),
                            args=[
                                ast.Constant(value=pickled_path),
                                ast.Constant(value="rb"),
                            ],
                            keywords=[],
                        ),
                        optional_vars=ast.Name(id="f", ctx=ast.Store()),
                    )
                ],
                body=[
                    # corresponds to parameter = dill.loads(f.read())
                    ast.Assign(
                        targets=[ast.Name(id=parameter, ctx=ast.Store())],
                        value=ast.Call(
                            func=ast.Attribute(
                                value=ast.Name(id="dill", ctx=ast.Load()),
                                attr="loads",
                                ctx=ast.Load(),
                            ),
                            args=[
                                ast.Call(
                                    func=ast.Attribute(
                                        value=ast.Name(id="f", ctx=ast.Load()),
                                        attr="read",
                                        ctx=ast.Load(),
                                    ),
                                    args=[],
                                    keywords=[],
                                )
                            ],
                            keywords=[],
                        ),
                    )
                ],
            ),
        )
        generated_ast = ast.fix_missing_locations(generated_ast)

        ret = ast.fix_missing_locations(
            ast.Return(value=ast.Name(id=parameter, ctx=ast.Load()))
        )

        return MetaFixture([], parameter, [generated_ast], ret)