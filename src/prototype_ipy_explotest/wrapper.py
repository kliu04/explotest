import IPython
from IPython.core.magic_arguments import magic_arguments


def generate_test(ipython: IPython.InteractiveShell):
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