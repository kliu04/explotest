import ast
import os
from dataclasses import dataclass
from typing import cast

import dill

from .abstract_fixture import AbstractFixture
from .helpers import is_primitive, random_id
from .reconstructor import Reconstructor


@dataclass
class PickleReconstructor(Reconstructor):

    def _ast(self, parameter, argument) -> AbstractFixture:
        if is_primitive(argument):
            return Reconstructor._reconstruct_primitive(parameter, argument)

        # create a unique ID for the pickled object
        pickled_id = random_id()

        # write the pickled object to file
        os.makedirs(f"{self.file_path.parent}/pickled", exist_ok=True)
        pickled_path = f"{self.file_path.parent}/pickled/{parameter}_{pickled_id}.pkl"
        with open(pickled_path, "wb") as f:
            f.write(dill.dumps(argument))

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

        return AbstractFixture([], parameter, [generated_ast], ret)
