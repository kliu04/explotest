from typing import Any
from IPython.terminal.embed import InteractiveShellEmbed


def id(x: Any) -> Any:
    return x


embedded_shell = InteractiveShellEmbed()
embedded_shell.run_line_magic("load_ext", "explotest.ipy")

embedded_shell()
