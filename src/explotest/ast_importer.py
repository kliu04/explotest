import ast
import importlib
import importlib.abc
import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from explotest.__main__ import ASTTracker
from explotest.ast_file import ASTFile
from explotest.ast_rewriter import ASTRewriterA


class Loader(importlib.abc.Loader):
    """Implement importlib.Loader"""

    def __init__(self, ctx: "ASTTracker", run_as_main: bool):
        self.run_as_main = run_as_main
        self.ctx = ctx

    def exec_module(self, module):
        path = Path(module.__file__)

        if self.ctx.get(path):
            # if the file has already been tracked, we can just use the previous one
            ast_file = self.ctx.get(path)
        else:

            # open the file, parse the AST, and rewrite it before running it
            with open(module.__file__) as f:
                src = f.read()

            if self.run_as_main:
                module.__dict__["__name__"] = "__main__"
                self.run_as_main = False
                if len(sys.argv) > 1:
                    src = f"import sys\nsys.argv = {sys.argv}\n" + src

            tree = ast.parse(src, module.__file__, "exec")
            ast_file = ASTFile(path.name, tree)
            ast_file.transform(ASTRewriterA())
            ast_file.reparse()
            self.ctx.add(path, ast_file)

        code = compile(ast_file.node, module.__file__, "exec")  # type: ignore
        exec(code, module.__dict__)

    def create_module(self, spec):
        return None  # Use default module creation


class Finder(importlib.abc.MetaPathFinder):
    """An importlib finder that will handler files from user code directory."""

    def __init__(self, code_dir, ctx):
        self.code_dir = code_dir
        self.run_as_main = True
        self.ctx = ctx

    def find_spec(self, fullname: str, path: list[str], target=None):
        # if path:
        #     mod_path = Path(path[0])
        #     if not mod_path.is_relative_to(self.code_dir):
        #         return None
        relative_path = fullname.replace(".", "/")  # json.decoder -> json/decoder
        full_path = self.code_dir / (relative_path + ".py")
        if not full_path.is_file():
            return None

        loader = Loader(self.ctx, self.run_as_main)
        self.run_as_main = False
        spec = importlib.util.spec_from_file_location(
            fullname, full_path, loader=loader
        )
        return spec
