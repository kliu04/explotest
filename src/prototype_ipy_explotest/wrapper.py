import IPython
from IPython.core.magic_arguments import magic_arguments, argument, parse_argstring

from .test_generator import TestGenerator


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
        '--lineno',
        dest='lineno',
        help="""
        Target line number.
        """
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
    def generate_tests_wrapped(parameter_s=''):
        args = parse_argstring(generate_tests_wrapped, parameter_s)
        with open(args.filename, 'w+') as file:
            generated_test = TestGenerator(ipython, int(args.lineno)).generate_test()
            file.write(str(generated_test))

    return generate_tests_wrapped
