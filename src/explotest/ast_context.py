from pathlib import Path

from explotest.ast_file import ASTFile


class ASTContext:
    def __init__(self):
        self.files: dict[Path, ASTFile] = {}

    def get(self, path: Path) -> ASTFile | None:
        return self.files.get(path)

    def add(self, path: Path, file: ASTFile):
        self.files[path] = file

    @property
    def all_files(self) -> list[ASTFile]:
        return list(reversed(self.files.values()))
