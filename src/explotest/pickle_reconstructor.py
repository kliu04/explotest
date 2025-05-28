import ast
import uuid
from pathlib import Path
from typing import cast

import dill  # type: ignore

from src.explotest.helpers import is_primitive
from src.explotest.pytest_fixture import PyTestFixture
from src.explotest.reconstructor import Reconstructor


class PickleReconstructor(Reconstructor):

    filepath: Path  # path to write the pickled files to

    def __init__(self, filepath):
        self.filepath = filepath

    def asts(self, bindings) -> list[PyTestFixture]:
        """:returns a list of PyTestFixture, which represents each parameter : argument pair"""
        fixtures = []
        for parameter, argument in bindings.items():
            if is_primitive(argument):
                fixtures.append(
                    PyTestFixture(
                        [],
                        parameter,
                        [
                            # need to cast here to not confuse mypy
                            cast(
                                ast.AST,
                                # assign each primitive its argument as a constant
                                # TODO: check if this works for collections
                                ast.Assign(
                                    targets=[ast.Name(id=parameter, ctx=ast.Store())],
                                    value=ast.Constant(value=argument),
                                ),
                            )
                        ],
                    )
                )

            else:
                # create a unique ID for the pickled object
                pickled_id = str(uuid.uuid4().hex)[:8]

                # write the pickled object to file
                pickled_path = f"{self.filepath}/pickled/{parameter}_{pickled_id}.pkl"
                with open(pickled_path, "wb") as f:
                    f.write(dill.dumps(argument))

                fixtures.append(
                    PyTestFixture(
                        [],
                        parameter,
                        [
                            cast(
                                ast.AST,
                                # with open(pickled_path, "rb") as f:
                                ast.With(
                                    items=[
                                        ast.withitem(
                                            context_expr=ast.Call(
                                                func=ast.Name(
                                                    id="open", ctx=ast.Load()
                                                ),
                                                args=[
                                                    ast.Constant(value=pickled_path),
                                                    ast.Constant(value="rb"),
                                                ],
                                                keywords=[],
                                            ),
                                            optional_vars=ast.Name(
                                                id="f", ctx=ast.Store()
                                            ),
                                        )
                                    ],
                                    body=[
                                        # param = dill.loads(f.read())
                                        ast.Assign(
                                            targets=[
                                                ast.Name(id=parameter, ctx=ast.Store())
                                            ],
                                            value=ast.Call(
                                                func=ast.Attribute(
                                                    value=ast.Name(
                                                        id="dill", ctx=ast.Load()
                                                    ),
                                                    attr="loads",
                                                    ctx=ast.Load(),
                                                ),
                                                args=[
                                                    ast.Call(
                                                        func=ast.Attribute(
                                                            value=ast.Name(
                                                                id="f", ctx=ast.Load()
                                                            ),
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
                        ],
                    )
                )
        return fixtures
