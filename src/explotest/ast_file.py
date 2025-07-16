import ast
from dataclasses import dataclass


@dataclass
class ASTFile:
    filename: str
    nodes: ast.Module
    traced_line_numbers: set[int]
    line_comments: list[int]

    def __init__(self, filename, nodes):
        self.filename = filename
        self.nodes = nodes
        self.traced_line_numbers = set()
        self.line_comments = list()
