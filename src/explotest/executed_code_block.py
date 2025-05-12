import io


class ExecutedCodeBlock:
    def __init__(self, start_lineno: int, end_lineno: int, file: io.TextIOWrapper):
        self.start_lineno = start_lineno
        self.end_lineno = end_lineno
        self.file = file
