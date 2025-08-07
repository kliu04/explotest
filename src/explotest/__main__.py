"""
Runs the ExploTest dynamic tracer and AST rewriter pipeline.

Namely:
- Sets a tracing hook to monitor executed lines during program execution.
- Applies pruning and rewriting passes to simplify the AST using both static and dynamic data.

Usage: python -m explotest <target.py>
"""

import importlib
import os
import sys
from pathlib import Path

from explotest.ast_context import ASTContext
from explotest.ast_importer import Finder


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
    import runpy

    runpy.run_path(os.path.abspath(target), run_name="__main__")

    # if not is_running_under_test():
    # TODO: make this work for modules
    # ctx = ASTContext()
    # tracer = make_tracer(ctx)
    # sys.settrace(tracer)
    # atexit.register(lambda: sys.settrace(None))
    # # the next line will run the code and rewriterA
    # load_code(Path(script_dir), Path(target).stem, ctx)
    # sys.settrace(None)


if __name__ == "__main__":
    main()
