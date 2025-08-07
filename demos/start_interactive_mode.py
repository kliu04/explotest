from IPython.terminal.embed import InteractiveShellEmbed

embedded_shell = InteractiveShellEmbed()
embedded_shell.run_line_magic("load_ext", "explotest.ipy")

embedded_shell()
