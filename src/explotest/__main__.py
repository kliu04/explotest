"""
Runs the ExploTest dynamic tracer and AST rewriter pipeline.

Namely:
- Sets a tracing hook to monitor executed lines during program execution.
- Applies pruning and rewriting passes to simplify the AST using both static and dynamic data.

Usage: python -m explotest <target.py>
"""
import atexit
import importlib
import os
import runpy
import sys
from pathlib import Path

from explotest.ast_context import ASTContext
from explotest.ast_importer import Finder
from explotest.tracer import make_tracer


def load_code(root_path: Path, module_name: str, ctx: ASTContext):
    """Load user code, patch function calls."""
    finder = Finder(root_path, ctx)
    try:
        # insert our custom finder into the "meta-path", import the module
        sys.meta_path.insert(0, finder)
        return importlib.import_module(module_name)
    finally:
        sys.meta_path.pop(0)


def main():

    if len(sys.argv) < 2:
        print("Usage: python3 -m explotest <filename>")
        sys.exit(1)

    target = sys.argv[1]
    target_folder = os.path.dirname(target)
    sys.argv = sys.argv[1:]

    script_dir = os.path.abspath(target_folder)
    sys.path.insert(0, script_dir)

    sys.settrace(make_tracer())
    atexit.register(lambda: sys.settrace(None))
    runpy.run_path(os.path.abspath(target), run_name="__main__")
    sys.settrace(None)


if __name__ == "__main__":
    main()
