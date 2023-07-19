import ast
from dataclasses import dataclass

from squall import util

SQLITE_EXECUTE_FUNCS = {"execute", "executescript", "executemany"}


@dataclass
class SquallError:
    error: str
    line: int

    def __str__(self) -> str:
        return f"{self.line}: {self.error}"


class SqliteStmtVisitor(ast.NodeVisitor):
    symbols: dict[str, str]
    errors: list[SquallError]

    def __init__(self) -> None:
        self.symbols = {}
        self.errors = []

    def visit_Import(self, node: ast.Import) -> None:
        self.generic_visit(node)

        for name in node.names:
            if name.name == "sqlite3":
                self.symbols[name.asname or name.name] = "sqlite3"

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.generic_visit(node)

        if node.module == "sqlite3":
            for name in node.names:
                if name.name == "connect":
                    self.symbols[name.asname or name.name] = "sqlite3.connect"

    def visit_Assign(self, node: ast.Assign) -> None:
        self.generic_visit(node)

        if not (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Call)
        ):
            return

        if self.is_connect_call(node.value) or self.is_sqlite3_connect_call(
            node.value
        ):
            self.symbols[node.targets[0].id] = "sqlite3.Connection"

    def visit_Call(self, node: ast.Call) -> None:
        self.generic_visit(node)

        if isinstance(node.func, ast.Attribute):
            callee = node.func.value

            if not (
                isinstance(callee, ast.Name)
                and self.symbols.get(callee.id) == "sqlite3.Connection"
            ):
                return

            if node.func.attr in SQLITE_EXECUTE_FUNCS:
                arg = node.args[0]

                if isinstance(arg, ast.Constant) and isinstance(
                    arg.value, str
                ):
                    # TODO: don't hardcode database here
                    error = util.validate("db.db3", arg.value)

                    if error:
                        self.errors.append(SquallError(error, line=arg.lineno))

    def is_connect_call(self, call: ast.Call) -> bool:
        return (
            isinstance(call.func, ast.Name)
            and self.symbols.get(call.func.id) == "sqlite3.connect"
        )

    def is_sqlite3_connect_call(self, call: ast.Call) -> bool:
        return (
            isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and self.symbols.get(call.func.value.id) == "sqlite3"
            and call.func.attr == "connect"
        )
