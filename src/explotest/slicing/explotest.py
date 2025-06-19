"""
Used only for slicing!
Sets up tracer that will track every executed line
"""

import ast
import dis
import os
import runpy
import sys
import sysconfig
import types
from collections import defaultdict

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IfTracker:
    start_lineno: int
    end_lineno: int
    path: Path
    stack_level: int


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


ast_cache: dict[Path, dict[int, list[ast.AST]]] = (
    {}
)  # open files -> (lineno -> ast) mapping
_map: dict[str, set[int]] = defaultdict(set)  # variable to lineno dependencies
_list: list[set[int]] = []  # stack of control flow dependencies
_control_flow: list[IfTracker] = (
    []
)  # stack of (filename, lineno) to signify when an if ends
_precall_args: list[list[set[int]]] = []
# stack of list of sets to keep track of dependencies of each parameter/arg
_precall_kwargs: list[dict[str, set[int]]] = []


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
            self.generic_visit(node)

    ContextFinder().visit(node)
    return res


def tracer(frame: types.FrameType, event, arg):
    """
    #     Hooks onto Python default tracer to add instrumentation for ExploTest.
    #     :param frame:
    #     :param event:
    #     :param __arg:
    #     :return: must return this object for tracing to work
    #"""
    filename = frame.f_globals.get("__file__", "<unknown>")
    frame.f_trace_opcodes = True
    bytecode = dis.Bytecode(frame.f_code)
    path = Path(filename)
    path.resolve()
    nodes = get_ast_nodes(path, frame.f_lineno)

    # ignore files we don't have access to
    if is_frozen_file(filename) or is_stdlib_file(filename) or is_venv_file(filename):
        return tracer

    # can do opcode or line
    if event == "line":
        instructions = list(
            filter(lambda instr: instr.line_number == frame.f_lineno, bytecode)
        )

        load = set()
        store = set()

        for instr in instructions:
            arg = instr.argrepr

            match instr.opname:
                case "LOAD_NAME" | "LOAD_FAST":
                    load.add(arg)
                case "STORE_NAME" | "STORE_FAST":
                    store.add(arg)
                case "LOAD_FAST_LOAD_FAST":
                    arg = map(str.strip, arg.split(",")) # convert str "(x, y)" to tuple ("x", "y")
                    for a in arg:
                        load.add(a)
                case "STORE_FAST_STORE_FAST":
                    arg = map(str.strip, arg.split(",")) # convert str "(x, y)" to tuple ("x", "y")
                    for a in arg:
                        store.add(a)

        depth = 0
        f = frame
        while f:
            depth += 1
            f = f.f_back

        match nodes[0]:
            case ast.If():
                _list.append(*map(_map.__getitem__, load))
                _control_flow.append(
                    IfTracker(nodes[0].lineno, nodes[0].end_lineno, path, depth)
                )

        for var in store:
            _map[var] = set().union(
                *map(_map.__getitem__, load), {frame.f_lineno}, *_list
            )

        while len(_control_flow) > 0:
            assert len(_control_flow) == len(_list)
            last_if = _control_flow[-1]
            if frame.f_lineno > last_if.end_lineno and last_if.stack_level == depth:
                _control_flow.pop()
                _list.pop()
            elif last_if.stack_level > depth:
                _control_flow.pop()
                _list.pop()
            else:
                break

        print(
            f"[{filename}:{frame.f_lineno}] -> AST Nodes: {_map} {_list} {_control_flow}"
        )
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
