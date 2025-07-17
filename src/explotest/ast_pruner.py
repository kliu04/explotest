import ast


class ASTPruner(ast.NodeTransformer):

    @staticmethod
    def check_executed(nodes: list[ast.AST]) -> bool:
        for node in nodes:
            for n in ast.walk(node):
                if getattr(n, "executed", False):
                    return True
        return False

    def visit_If(self, node):

        # visit children recursively
        super().generic_visit(node)

        if not node.orelse:
            return node

        body_was_executed = ASTPruner.check_executed(node.body)
        else_was_executed = ASTPruner.check_executed(node.orelse)
        print(ast.dump(node, include_attributes=True), "!!!")

        if (body_was_executed and else_was_executed) or (
            not body_was_executed and not else_was_executed
        ):
            # both were executed, say in a loop
            return node
        elif body_was_executed:
            # only the body was executed
            return node.body
        else:
            # only else was executed
            return node.orelse

    def visit_For(self, node):
        super().generic_visit(node)

        body_was_executed = ASTPruner.check_executed(node.body)

        # condition is false
        if not body_was_executed:
            return None
        return node

    def visit_FunctionDef(self, node):
        super().generic_visit(node)

        body_was_executed = ASTPruner.check_executed(node.body)
        if not body_was_executed:
            node.body = [ast.Pass()]
        return node

    def visit_Try(self, node):
        super().generic_visit(node)
        handler_was_executed = ASTPruner.check_executed(node.handlers)

        if not handler_was_executed:
            if node.orelse or node.finalbody:
                # change catching exception to pass
                return ast.Try(
                    node.body,
                    [
                        ast.ExceptHandler(
                            type=ast.Name(id="Exception", ctx=ast.Load()),
                            name="e",
                            body=[ast.Pass()],
                        )
                    ],
                    node.orelse,
                    node.finalbody,
                )
            else:
                return node.body

        # remove else since exception was raised
        return ast.Try(
            node.body,
            node.handlers,
            [],
            node.finalbody,
        )
