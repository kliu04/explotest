import ast
from dataclasses import dataclass


@dataclass
class ASTFile:
    nodes: ast.Module
    traced_line_numbers: set[int]
    line_comments: list[int]

    def __init__(self, nodes):
        self.nodes = nodes
        self.traced_line_numbers = set()
        self.line_comments = list()
