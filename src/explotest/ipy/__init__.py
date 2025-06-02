import IPython
from IPython.core.magic import register_line_magic

from .wrapper import generate_tests_wrapper
__version__ = "0.1.5"


def load_ipython_extension(ipython: IPython.InteractiveShell):
    register_line_magic(generate_tests_wrapper(ipython))