"""
Used only for slicing!
Sets up tracer that will track every executed line
"""

import ast
import inspect
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


ast_cache: dict[Path, dict[int, list[ast.AST]]] = (
    {}
)  # open files -> (lineno -> ast) mapping
_map: dict[str, set[int]] = defaultdict(set)  # variable to lineno dependencies
_list: list[set[int]] = [set()]  # stack of control flow dependencies
_control_flow: list[tuple[Path, int]] = (
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


def tracer(frame, event, __arg):
    """
    Hooks onto Python default tracer to add instrumentation for ExploTest.
    :param frame:
    :param event:
    :param __arg:
    :return: must return this object for tracing to work
    """
    lineno = frame.f_lineno
    filename = frame.f_globals.get("__file__", "<unknown>")

    # ignore files we don't have access to
    if is_frozen_file(filename) or is_stdlib_file(filename) or is_venv_file(filename):
        return tracer

    path = Path(filename)
    path.resolve()

    nodes = get_ast_nodes(path, lineno)

    if event == "call":

        # python interpreter interprets loading a module as calling a function wrapper of the module
        if frame.f_lineno == 0:
            return tracer

        last_precall = _precall_args.pop()
        last_precall_kw = _precall_kwargs.pop()

        func = frame.f_globals[frame.f_code.co_name]
        signature = inspect.signature(func)

        num_positional_args = len(last_precall)
        pos_index = 0

        # TODO: arrays, objects, varkw, varargs, aliasing
        print(signature.parameters, last_precall)

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
        match nodes[0]:
            # AugAssign is +=, *=, etc.
            case ast.Assign() | ast.AugAssign():
                for var in get_context_id(nodes[0], ast.Store()):
                    # union of the current line,
                    # the sets each of the rvalues of the assignment map to in _map, and
                    # the line numbers currently stored in any elements of list
                    _map[var] = set().union(
                        {lineno},
                        *map(_map.__getitem__, get_context_id(nodes[0], ast.Load())),
                        *_list,
                    )
            case ast.If():
                # before an if-then-else we add code to calculate the set s
                # of all current dependencies of variables in the loop/branch condition,
                # and push this onto our current list _list

                union = set().union(
                    *map(_map.__getitem__, get_context_id(nodes[0].test, ast.Load()))
                )
                _list.append(union)
                _control_flow.append((path, nodes[0].end_lineno))

            case ast.For():
                # In for example, "for i in range(n)", i is the target
                # i is being assigned, so follow the assignment rules
                for target in get_context_id(nodes[0].target, ast.Store()):
                    _map[target] = set().union(
                        {lineno},
                        # i depends on n in the above
                        *map(
                            _map.__getitem__, get_context_id(nodes[0].iter, ast.Load())
                        ),
                        *_list,
                    )

                # This does not follow 410 exactly, because we add and pop outside the loop,
                # Add code to calculate the set of all current dependencies of variables in the loop condition,
                # and push this onto our current list _list
                # The branch condition dependencies are replaced at every loop iteration
                _list.append(
                    set().union(
                        {lineno},
                        *map(
                            _map.__getitem__, get_context_id(nodes[0].iter, ast.Load())
                        ),
                    )
                )
                _control_flow.append((path, nodes[0].end_lineno))
            case ast.While():
                _list.append(
                    set().union(
                        {lineno},
                        *map(
                            _map.__getitem__, get_context_id(nodes[0].test, ast.Load())
                        ),
                    )
                )
                _control_flow.append((path, nodes[0].end_lineno))

        for node in nodes:
            # print(ast.dump(node, indent=4))
            if isinstance(node, ast.Call):

                bindings = [
                    _map[var]
                    for arg in node.args
                    for var in get_context_id(arg, ast.Load())
                ]
                _precall_args.append(bindings)
                kw_bindings = {
                    arg.arg: _map[var]
                    for arg in node.keywords
                    for var in get_context_id(arg, ast.Load())
                }
                _precall_kwargs.append(kw_bindings)

        # pop control flow after we exit
        while (
            len(_control_flow) > 0
            and nodes[0].lineno >= _control_flow[-1][1]
            and path == _control_flow[-1][0]
        ):
            _control_flow.pop()
            _list.pop()

        print(
            f"[{filename}:{lineno}] -> AST Nodes: {_map} {_list} {_control_flow} {_precall_args}"
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
