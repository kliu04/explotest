"""
Used only for slicing!
Sets up tracer that will track every executed line
"""

import ast
import dis
import inspect
import os
import runpy
import sys
import sysconfig
import types
from collections import defaultdict

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ControlFlowTracker:
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
_control_flow: list[ControlFlowTracker] = (
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
    """
    filename = frame.f_globals.get("__file__", "<unknown>")
    frame.f_trace_opcodes = True
    bytecode = dis.Bytecode(frame.f_code)
    path = Path(filename)
    path.resolve()
    lineno = frame.f_lineno
    nodes = get_ast_nodes(path, lineno)

    # ignore files we don't have access to
    if is_frozen_file(filename) or is_stdlib_file(filename) or is_venv_file(filename):
        return tracer

    if event == "call":

        # python interpreter interprets loading a module as calling a function wrapper of the module
        if lineno == 0:
            return tracer

        last_precall = _precall_args.pop()
        last_precall_kw = _precall_kwargs.pop()

        func = frame.f_globals[frame.f_code.co_name]
        signature = inspect.signature(func)

        num_positional_args = len(last_precall)
        pos_index = 0

        for parameter in signature.parameters.values():
            name = parameter.name
            match parameter.kind:
                case inspect.Parameter.POSITIONAL_ONLY:
                    if pos_index < num_positional_args:
                        _map[name] = last_precall[pos_index] | {lineno}
                        pos_index += 1
                    else:
                        raise AssertionError("This should never happen.")
                case inspect.Parameter.POSITIONAL_OR_KEYWORD:
                    if name in last_precall_kw:
                        _map[name] = last_precall_kw[name] | {lineno}
                    elif pos_index < num_positional_args:
                        _map[name] = last_precall[pos_index] | {lineno}
                        pos_index += 1
                    else:
                        _map[name] = {lineno}  # default argument
                case inspect.Parameter.VAR_POSITIONAL:
                    pass  # not yet implemented
                case inspect.Parameter.KEYWORD_ONLY:
                    if name in last_precall_kw:
                        _map[name] = last_precall_kw[name] | {lineno}
                    else:
                        _map[name] = {lineno}  # default argument
                case inspect.Parameter.VAR_KEYWORD:
                    pass  # not yet implemented

    elif event == "line":
        instructions = list(filter(lambda instr: instr.line_number == lineno, bytecode))

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
                    arg = map(
                        str.strip, arg.split(",")
                    )  # convert str "(x, y)" to tuple ("x", "y")
                    for a in arg:
                        load.add(a)
                case "STORE_FAST_STORE_FAST":
                    arg = map(
                        str.strip, arg.split(",")
                    )  # convert str "(x, y)" to tuple ("x", "y")
                    for a in arg:
                        store.add(a)

        depth = 0
        f = frame
        while f:
            depth += 1
            f = f.f_back

        while len(_control_flow) > 0:
            assert len(_control_flow) == len(_list)
            last_if = _control_flow[-1]
            if (
                lineno >= last_if.end_lineno
                and last_if.stack_level == depth
                and last_if.path == path
            ):
                _control_flow.pop()
                _list.pop()
            elif last_if.stack_level > depth:
                _control_flow.pop()
                _list.pop()
            else:
                break

        match nodes[0]:
            case ast.If():
                # before an if-then-else we add code to calculate the set s
                # of all current dependencies of variables in the loop/branch condition,
                # and push this onto our current list _list
                _list.append(set().union(*map(_map.__getitem__, load)))
                _control_flow.append(
                    ControlFlowTracker(
                        nodes[0].lineno, nodes[0].end_lineno, path, depth
                    )
                )

            case ast.For() | ast.While():
                # Add code to calculate the set of all current dependencies of variables in the loop condition,
                # and push this onto our current list _list
                # The branch condition dependencies are replaced at every loop iteration
                _list.append(set().union(*map(_map.__getitem__, load), {lineno}))
                _control_flow.append(
                    ControlFlowTracker(
                        nodes[0].lineno, nodes[0].end_lineno, path, depth
                    )
                )

        for node in nodes:
            # print(ast.dump(node, indent=4))
            if isinstance(node, ast.Call):

                bindings = [
                    _map[var] | {lineno}
                    for arg in node.args
                    for var in get_context_id(arg, ast.Load())
                ]
                _precall_args.append(bindings)
                kw_bindings = {
                    arg.arg: _map[var] | {lineno}
                    for arg in node.keywords
                    for var in get_context_id(arg, ast.Load())
                }
                _precall_kwargs.append(kw_bindings)

        for var in store:
            # union of the current line,
            # the sets each of the rvalues of the assignment map to in _map, and
            # the line numbers currently stored in any elements of list
            _map[var] = set().union(*map(_map.__getitem__, load), {lineno}, *_list)

        print(
            f"[{filename}:{lineno}] -> AST Nodes: {_map} {_list} {_control_flow} {depth}"
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
