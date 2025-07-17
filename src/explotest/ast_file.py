"""
Data Structure that represents a File, with associated filename, AST, and line numbers that have been executed

"""

import ast
from dataclasses import dataclass


@dataclass
class ASTFile:
    filename: str
    nodes: ast.Module
    executed_line_numbers: set[int]

    def __init__(self, filename, nodes):
        self.filename = filename
        self.nodes = nodes
        self.executed_line_numbers = set()
