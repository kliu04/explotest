import ast
import importlib
import importlib.abc
import importlib.util
from pathlib import Path

from explotest.ast_file import ASTFile
from explotest.ast_rewriter import ASTRewriterA

tracked_files: dict[Path, ASTFile] = {}


class Loader(importlib.abc.Loader):
    """Implement importlib.Loader"""

    def __init__(self, run_as_main):
        self.run_as_main = run_as_main

    def exec_module(self, module):

        with open(module.__file__) as f:
            src = f.read()

        path = Path(module.__file__)
        if tracked_files.get(path):
            patched_tree = tracked_files[path].nodes
        else:
            tree = ast.parse(src, module.__file__, "exec")
            ast_file = ASTFile(path.name, tree)
            trans = ASTRewriterA(ast_file)
            patched_tree = trans.rewrite()
            # print(ast.dump(patched_tree, indent=4, include_attributes=True))
            # print(ast.dump(ast.parse(ast.unparse(patched_tree)), indent=4, include_attributes=True))
            patched_tree = ast.parse(ast.unparse(patched_tree))
            ast.fix_missing_locations(patched_tree)
            ast_file.nodes = patched_tree
            tracked_files[path] = ast_file

        code = compile(patched_tree, module.__file__, "exec")

        if self.run_as_main:
            module.__dict__["__name__"] = "__main__"
            self.run_as_main = False
        exec(code, module.__dict__)

    def create_module(self, spec):
        return None  # Use default module creation


class Finder(importlib.abc.MetaPathFinder):
    """An importlib finder that will handler files from user code directory."""

    def __init__(self, code_dir):
        self.code_dir = code_dir
        self.run_as_main = True

    def find_spec(self, fullname: str, path: list[str], target=None):
        # if path:
        #     mod_path = Path(path[0])
        #     if not mod_path.is_relative_to(self.code_dir):
        #         return None
        relative_path = fullname.replace(".", "/")  # json.decoder -> json/decoder
        full_path = self.code_dir / (relative_path + ".py")
        if not full_path.is_file():
            return None

        loader = Loader(self.run_as_main)
        self.run_as_main = False
        spec = importlib.util.spec_from_file_location(
            fullname, full_path, loader=loader
        )
        return spec
