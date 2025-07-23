import ast
import copy
from abc import abstractmethod
from typing import cast

from explotest import helpers
from explotest.ast_file import ASTFile


class ASTRewriter(ast.NodeTransformer):

    queue: list[tuple[list[ast.AST], ast.AST]]
    ast_file: ASTFile

    def __init__(self, ast_file: ASTFile):
        self.queue = []
        self.ast_file = ast_file

    @abstractmethod
    def rewrite(self): ...

    @staticmethod
    def is_simple(arg):
        return isinstance(arg, (ast.Constant, ast.Name))

    @staticmethod
    def ancestor_in_body(n, body):

        if n is None:
            return None
        if n in body:
            return n, body
        return ASTRewriter.ancestor_in_body(n.parent, body)

    @staticmethod
    def insert_assignments(assignments, node):

        parent = node.parent
        # walk up to find a parent that has a "body" list containing the node

        while parent:
            for attr in ["body", "orelse", "finalbody"]:
                if hasattr(parent, attr):
                    body = getattr(parent, attr)
                    if isinstance(body, list) and (
                        t := ASTRewriter.ancestor_in_body(node, body)
                    ):
                        index = t[1].index(t[0])
                        body[index:index] = assignments  # insert before
                        return
            parent = parent.parent

        raise RuntimeError("Cannot find place to insert assignments.")


class ASTRewriterA(ASTRewriter):

    def visit_Assign(self, node):
        self.generic_visit(node)

        if isinstance(node.value, ast.IfExp):
            body = ast.Assign(
                targets=[copy.copy(node.targets[0])], value=node.value.body
            )
            orelse = ast.Assign(
                targets=[copy.copy(node.targets[0])], value=node.value.orelse
            )

            new_node = ast.If(
                node.value.test,
                [body],
                [orelse],
            )
            return new_node
        return node

    def visit_If(self, node):
        self.generic_visit(node)
        if not node.orelse:
            new_node = ast.Pass()
            node.orelse = [new_node]
        return node

    def rewrite(self):
        node = self.ast_file.nodes
        new_node = self.visit(node)
        ast.fix_missing_locations(new_node)
        return new_node


class ASTRewriterB(ASTRewriter):
    def visit_Assign(self, node: ast.Assign):
        """
        unpacks tuple assignments and ifexp assignments
        """
        self.generic_visit(node)

        # check for a tuple unpacking assignment
        if (
            isinstance(node.targets[0], ast.Tuple)
            and isinstance(node.value, ast.Tuple)
            and len(node.targets[0].elts) == len(node.value.elts)
        ):
            new_variables = list(zip(node.targets[0].elts, node.value.elts))
            new_nodes = [
                ast.Assign(targets=[target], value=value)
                for target, value in new_variables
            ]
            if getattr(node, "executed", False):
                for node in new_nodes:
                    node.executed = True

            return new_nodes

        return node

    def visit_Call(self, node):
        """
        unpack expressions in call contexts
        """
        self.generic_visit(node)

        lis = []
        names = []
        for i, arg in enumerate(node.args):
            temp_name = helpers.uniquify("temp")
            if ASTRewriter.is_simple(arg):
                continue
            elif isinstance(arg, ast.Starred):
                assign = ast.Assign(
                    targets=[ast.Name(id=temp_name, ctx=ast.Store())],
                    value=arg.value,
                )
                names.append(temp_name)

            else:
                assign = ast.Assign(
                    targets=[ast.Name(id=temp_name, ctx=ast.Store())], value=arg
                )
                names.append(temp_name)
            assign.executed = getattr(node, "executed", False)
            lis.append(assign)
        self.queue.append((lis, node))

        lis = []
        # the actual args in the call
        names = iter(names)
        for arg in node.args:
            if ASTRewriter.is_simple(arg):
                lis.append(arg)
            elif isinstance(arg, ast.Starred):
                lis.append(
                    ast.Starred(
                        value=ast.Name(id=next(names), ctx=ast.Load()), ctx=arg.ctx
                    )
                )
            else:
                lis.append(ast.Name(id=next(names), ctx=ast.Load()))

        node.args = lis
        return node

    def visit_Subscript(self, node):
        self.generic_visit(node)

        if isinstance(node.slice, ast.Slice):

            assignments = []
            slice_kwargs = {}

            if node.slice.lower:
                if not ASTRewriter.is_simple(node.slice.lower):
                    temp_name = helpers.uniquify("temp")
                    assign = ast.Assign(
                        targets=[ast.Name(id=temp_name, ctx=ast.Store())],
                        value=node.slice.lower,
                    )
                    assign.executed = getattr(node, "executed", False)
                    assignments.append(assign)
                    slice_kwargs["lower"] = ast.Name(id=temp_name, ctx=ast.Load())
                else:
                    slice_kwargs["lower"] = node.slice.lower

            if node.slice.upper:
                if not ASTRewriter.is_simple(node.slice.upper):
                    temp_name = helpers.uniquify("temp")
                    assign = ast.Assign(
                        targets=[ast.Name(id=temp_name, ctx=ast.Store())],
                        value=node.slice.upper,
                    )
                    assign.executed = getattr(node, "executed", False)
                    assignments.append(assign)
                    slice_kwargs["upper"] = ast.Name(id=temp_name, ctx=ast.Load())
                else:
                    slice_kwargs["upper"] = node.slice.upper

            if assignments:
                self.queue.append((assignments, node))
                node.slice = ast.Slice(**slice_kwargs)

            return node
        elif ASTRewriter.is_simple(node.slice):
            return node
        else:
            temp_name = helpers.uniquify("temp")
            assign = ast.Assign(
                targets=[ast.Name(id=temp_name, ctx=ast.Store())],
                value=node.slice,
            )
            assign.executed = getattr(node, "executed", False)
            self.queue.append(
                (  # type: ignore
                    [
                        assign,
                    ],
                    node,
                )
            )
            node.slice = ast.Name(temp_name, ctx=ast.Load())
            return node

    def visit_FunctionDef(self, node):
        self.generic_visit(node)

        # remove docstrings
        if isinstance(node.body[0], ast.Expr):
            expr = cast(ast.Expr, node.body[0])
            if isinstance(expr.value, ast.Constant):
                potential_docstring = expr.value.value
                if type(potential_docstring) is str:
                    node.body = node.body[1:]
                    if not node.body:
                        # potentially, a function could only have a docstring and nothing else (god knows why)
                        node.body = [ast.Pass()]

        return node

    def rewrite(self):
        """
        Use this instead of visit!!!
        :return:
        """
        node = self.ast_file.nodes
        node.parent = None
        for n in ast.walk(node):
            # mark nodes that are ran
            for child in ast.iter_child_nodes(n):
                child.parent = n

        new_node = self.visit(node)
        for assignments, n in self.queue:
            ASTRewriter.insert_assignments(assignments, n)
        ast.fix_missing_locations(new_node)
        self.queue.clear()
        return new_node
