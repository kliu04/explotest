import IPython
from IPython.core.magic import register_line_magic

from .explotest import transform_tests_wrapper

__version__ = "0.1.5"


def load_ipython_extension(ipython: IPython.InteractiveShell):
    register_line_magic(transform_tests_wrapper(ipython))
