### Used only for slicing!
### Sets up tracer that will track every executed line
import ast
import os
import runpy
import sys
import sysconfig
from collections import defaultdict
from pathlib import Path


# TODO: check if OS independent
def is_stdlib_file(filepath: str) -> bool:
    """Determine if a file is part of the standard library;
    E.g., /Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/..."""
    stdlib_path = sysconfig.get_path("stdlib")
    abs_filename = os.path.abspath(filepath)
    abs_stdlib_path = os.path.abspath(stdlib_path)
    return abs_filename.startswith(abs_stdlib_path)


def is_venv_file(filepath: str) -> bool:
    return ".venv" in filepath


def is_frozen_file(filepath: str) -> bool:
    return filepath.startswith("<frozen ")


# cache: path -> { lineno -> [AST nodes] }
ast_cache = {}
_map: dict[str, set[int]] = defaultdict(set)
_list: list[set[int]] = [set()]
_control_flow: list[tuple[Path, int]] = []


class LineAstMapper(ast.NodeVisitor):
    """Walks the AST to map each lineno to corresponding AST nodes"""

    def __init__(self):
        self.line_to_nodes = defaultdict(list)

    def generic_visit(self, node):
        if hasattr(node, "lineno"):
            self.line_to_nodes[node.lineno].append(node)
        super().generic_visit(node)


def parse_ast(path: Path) -> dict[int, list[ast.AST]]:
    """Parses the file represented by path into a map of lineno to AST nodes"""
    source = path.read_text()
    tree = ast.parse(source, filename=path.name)
    mapper = LineAstMapper()
    mapper.visit(tree)
    return mapper.line_to_nodes


def get_ast_nodes(path: Path, lineno: int) -> list[ast.AST]:
    """Saves a cache of previously opened files"""
    if path not in ast_cache:
        ast_cache[path] = parse_ast(path)
    return ast_cache[path].get(lineno, [])


def get_context_id(node: ast.AST, context: ast.expr_context) -> list[str]:
    """searches for load or store contexts"""
    res: list[str] = []

    class ContextFinder(ast.NodeVisitor):
        """Walks the AST to map each lineno to corresponding AST nodes"""

        def visit_Name(self, node: ast.Name):
            if isinstance(node.ctx, type(context)):
                res.append(node.id)

    ContextFinder().visit(node)
    return res


def tracer(frame, event, arg):
    """
    Hooks onto Python default tracer to add instrumentation for ExploTest.
    :param frame:
    :param event:
    :param arg:
    :return: must return this object for tracing to work
    """
    if event == "line":
        lineno = frame.f_lineno
        filename = frame.f_globals.get("__file__", "<unknown>")
        if (
            is_frozen_file(filename)
            or is_stdlib_file(filename)
            or is_venv_file(filename)
        ):
            return tracer
        path = Path(filename)
        path.resolve()
        nodes = get_ast_nodes(path, lineno)

        # match type(nodes[0]):
        #     case "<class 'list'>":
        #         pass

        # AugAssign is +=, *=, etc.
        if isinstance(nodes[0], ast.Assign) or isinstance(nodes[0], ast.AugAssign):
            for x in get_context_id(nodes[0], ast.Store()):
                _map[x] = (
                    {lineno}
                    | set().union(
                        *map(_map.__getitem__, get_context_id(nodes[0], ast.Load()))
                    )
                    | _list[-1]
                )

        # somehow need to pop
        if isinstance(nodes[0], ast.If):
            _list.append(
                set().union(
                    *map(_map.__getitem__, get_context_id(nodes[0].test, ast.Load()))
                )
            )
            _control_flow.append((path, nodes[0].end_lineno))

        if isinstance(nodes[0], ast.For):
            for target in get_context_id(nodes[0].target, ast.Store()):
                _map[target] = set().union({lineno} , *map(_map.__getitem__, get_context_id(nodes[0].iter, ast.Load())))
            _list.append(
                set().union(
                    *map(_map.__getitem__, get_context_id(nodes[0].iter, ast.Load())),
                    {nodes[0].lineno},
                    
                )
            )
            _control_flow.append((path, nodes[0].end_lineno))

        if isinstance(nodes[0], ast.While):
            pass

        while (
            len(_control_flow) > 0
            and nodes[0].lineno >= _control_flow[-1][1]
            and path == _control_flow[-1][0]
        ):
            _control_flow.pop()
            _list.pop()

        print(f"[{filename}:{lineno}] -> AST Nodes: {_map} {_list} {_control_flow}")
        # for n in nodes:
        #     print(ast.dump(n, indent=4))

    return tracer


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 -m explotest <filename>")
        sys.exit(1)
    target = sys.argv[1]
    sys.argv = sys.argv[1:]

    script_dir = os.path.abspath(os.path.dirname(target))
    sys.path.insert(0, script_dir)

    sys.settrace(tracer)
    runpy.run_path(target, run_name="__main__")
    sys.settrace(None)


if __name__ == "__main__":
    main()
