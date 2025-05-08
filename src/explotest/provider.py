from abc import ABC, abstractmethod
import ast


class Provider(ABC):

    @abstractmethod
    def generate_active_ast(self) -> list[ast.AST]: ...

    @abstractmethod
    def generate_program_states(self) -> any: ...
