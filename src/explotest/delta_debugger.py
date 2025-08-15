import ast
import inspect
import sys

from explotest.ast_file import ASTFile
from explotest.oracle import Oracle


def ddmin(ast_file: ASTFile, arg: inspect.BoundArguments, oracle: Oracle) -> ast.AST:
    # FIXME: only works for 1 fut
    """
    :param ast_file: Representation of the file to delta debug
    :param arg: run-time arguments of the function-under-test
    :return: AST of the delta debugged file
    """
    seen: set[tuple[tuple[int, int], ...]] = set()
    collected_args: list[inspect.BoundArguments] = []
    ## KEEP A LIST OF TRACE INFO

    def get_max_lineno(node: ast.AST):
        """
        :param node: ast node
        :return: the largest line number of the ast, if it exists
        """
        return max(
            (n.lineno for n in ast.walk(node) if hasattr(n, "lineno")), default=0
        )

    # subset transformer
    class LineFilter(ast.NodeTransformer):
        def __init__(self, begin, end, keep: bool):
            super().__init__()
            self.begin = begin
            self.end = end
            self.keep = keep

        def visit(self, node):
            # if this node has a lineno, decide to keep or drop it
            if hasattr(node, "lineno"):
                in_range = self.begin <= node.lineno <= self.end
                # drop if in range and do not keep, or out of range and keep
                if in_range != self.keep:
                    return None
            return super().visit(node)

    def tracer(frame, event, arg):
        """
        Adds the run-time arguments of the function-under-test to the set seen_args
        :param frame: current stack frame
        :param event: trace event
        :param arg: unused
        :return:
        """
        if event == "call":
            fn = frame.f_globals.get(frame.f_code.co_name) or frame.f_locals.get(
                frame.f_code.co_name
            )
            if hasattr(fn, "__data__"):
                collected_args.append(fn.__data__.args)
        return tracer

    def run(node_ast: ast.AST) -> bool:
        """
        Test if running node_ast produces the same run-time arguments as in seen_args (oracle)
        :param node_ast: AST to run
        :return: arguments are the same
        """
        collected_args.clear()
        sys.settrace(tracer)

        try:
            # FIXME: don't actually know which arg should be compared against...
            return_value = oracle.run(node_ast, collected_args)
        except:
            sys.settrace(None)
            return False
        sys.settrace(None)
        return return_value

    def ddmin2(tree: ast.AST, n: int, test_subset: bool) -> ast.AST:
        """
        Main delta debugging function
        :param tree: AST of the program to delta debug
        :param n: number of subsets
        :param test_subset: whether to test subset or not
        :return: AST of the delta debugged program
        """
        # print(ast.unparse(tree))
        total_lines = get_max_lineno(tree)
        if total_lines == 0:
            raise Exception("something bad happened :(")

        tree = ast.parse(ast.unparse(tree))

        # compute chunk boundaries, distributing remainder
        base, rem = divmod(total_lines, n)
        boundaries: list[tuple[int, int]] = []
        start = 1
        for i in range(n):
            size = base + (1 if i < rem else 0)
            end = start + size - 1
            boundaries.append((start, end))
            start = end + 1

        # optimization
        if tuple(boundaries) in seen:
            return tree
        seen.add(tuple(boundaries))

        if test_subset:
            # reduce to subset
            for begin, end in boundaries:
                sub = LineFilter(begin, end, keep=True).visit(copy.deepcopy(tree))
                if run(sub):
                    return ddmin2(sub, 2, True)

        # reduce to complement
        for begin, end in boundaries:
            comp = LineFilter(begin, end, keep=False).visit(copy.deepcopy(tree))
            if run(comp):
                return ddmin2(comp, max(n - 1, 2), False)

        # increase granularity
        if n < total_lines:
            return ddmin2(tree, min(total_lines, 2 * n), True)

        return tree

    return ddmin2(ast_file.node, 2, False)
