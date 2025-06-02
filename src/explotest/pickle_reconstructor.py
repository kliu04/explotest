import ast
import os
import uuid
from dataclasses import dataclass
from typing import cast

import dill  # type: ignore

from src.explotest.helpers import is_primitive
from src.explotest.pytest_fixture import PyTestFixture
from src.explotest.reconstructor import Reconstructor


@dataclass(frozen=True)
class PickleReconstructor(Reconstructor):

    def _ast(self, parameter, argument) -> PyTestFixture:
        if is_primitive(argument):
            return Reconstructor._reconstruct_primitive(parameter, argument)

        # create a unique ID for the pickled object
        pickled_id = str(uuid.uuid4().hex)[:8]

        # write the pickled object to file
        os.makedirs(f"{self.file_path.parent}/pickled", exist_ok=True)
        pickled_path = f"{self.file_path.parent}/pickled/{parameter}_{pickled_id}.pkl"
        with open(pickled_path, "wb") as f:
            f.write(dill.dumps(argument))

        generated_ast = cast(
            ast.AST,
            # with open(pickled_path, "rb") as f:
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
                    # parameter = dill.loads(f.read())
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

        return PyTestFixture([], parameter, [generated_ast], ret)
