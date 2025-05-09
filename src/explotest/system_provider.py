import ast
import provider


class SystemProvider(provider.Provider):

    def generate_active_ast(self) -> list[ast.AST]:
        return []

    def generate_program_states(self) -> any:
        return []
