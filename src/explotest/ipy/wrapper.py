import IPython
import IPython.core.magic_arguments
from IPython.core.magic_arguments import magic_arguments, argument

from explotest import Mode, explore


def generate_tests_wrapper(ipython: IPython.InteractiveShell):
    @magic_arguments()
    # @argument(
    #     "-f",
    #     dest="filename",
    #     help="""
    #     FILENAME: instead of printing the output to the screen, redirect
    #     it to the given file.  The file is always overwritten, though *when
    #     it can*, IPython asks for confirmation first. In particular, running
    #     the command 'history -f FILENAME' from the IPython Notebook
    #     interface will replace FILENAME even if it already exists *without*
    #     confirmation.
    #     """,
    # )
    @argument(
        "--mode",
        dest="mode",
        help="""
        The method to re-create the args with.
        """,
    )
    @argument(
        "--function",
        dest="function",
        help="""
    test""",
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

        function_name: str = args.function

        print(f"function_name {function_name}")
        # history = ipython.history_manager.get_range(output=True)
        # for entry in history:
        #     print(entry)

        return explore(func=args.function, mode=mode)

    return generate_tests
