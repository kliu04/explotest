import IPython
from .extension import ExplotestMagics

__version__ = "0.1.5"


def load_ipython_extension(ipython: IPython.InteractiveShell):
    ipython.register_magics(ExplotestMagics)
