import ast
from pathlib import Path

import IPython
import IPython.core.magic_arguments
from IPython.core.magic_arguments import magic_arguments, argument

from src.explotest.helpers import Mode
from .frontend import FrontEnd
from ..test_generator import TestGenerator


def generate_tests_wrapper(ipython: IPython.InteractiveShell):
    @magic_arguments()
    @argument(
        "-f",
        dest="filename",
        help="""
        FILENAME: instead of printing the output to the screen, redirect
        it to the given file.  The file is always overwritten, though *when
        it can*, IPython asks for confirmation first. In particular, running
        the command 'history -f FILENAME' from the IPython Notebook
        interface will replace FILENAME even if it already exists *without*
        confirmation.
        """,
    )
    @argument(
        "--lineno",
        dest="lineno",
        help="""
        Target line number.
        """,
    )
    @argument(
        "--mode",
        dest="mode",
        help="""
        The method to re-create the args with.
        """,
    )
    # @argument(
    #     '--start',
    #     dest='start',
    #     help="""
    #     Start reading lines from here
    #     """
    # )
    # @argument(
    #     '--end',
    #     dest='end',
    #     help="""
    #     End reading lines here (inclusive)
    #     """
    # )
    def generate_tests(parameter_s=""):
        args = IPython.core.magic_arguments.parse_argstring(generate_tests, parameter_s)
        mode = None
        if args.mode == "pickle":
            mode = Mode.PICKLE
        elif args.mode == "reconstruct":
            mode = Mode.RECONSTRUCT
        elif args.mode == "slice":
            mode = Mode.SLICE
            raise NotImplementedError("Slice is not implemented yet.")

        ipy_frontend = FrontEnd(ipython, int(args.lineno))

        tg = TestGenerator(ipy_frontend.call_on_lineno.func.id, Path("."), mode)
        generated_test = tg.generate(
            ipy_frontend.function_params_and_args(),
            definitions=[ipy_frontend.function_def],
            injected_imports=ipy_frontend.repl_imports,
        )
        with open(args.filename, "w+") as file:
            file.write(ast.unparse(generated_test.ast_node))
        return generated_test

    return generate_tests
