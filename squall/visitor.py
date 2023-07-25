import ast
from dataclasses import dataclass

from squall import util
from squall.settings import Settings

SQLITE_EXECUTE_FUNCS = {"execute", "executescript", "executemany"}
SQL_EXECUTABLE_LIKE = {"sqlite3.Connection", "sqlite3.Cursor"}


@dataclass
class SquallError:
    error: str
    line: int

    def __str__(self) -> str:
        return f"{self.line}: {self.error}"


class SqliteStmtVisitor(ast.NodeVisitor):
    symbols: dict[str, str]
    errors: list[SquallError]

    settings: Settings | None

    def __init__(self, settings: Settings | None = None) -> None:
        self.symbols = {}
        self.errors = []
        self.settings = settings

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

        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            return

        self.update_symbol_table(node.targets[0].id, node.value)

    def visit_Call(self, node: ast.Call) -> None:
        self.generic_visit(node)

        if isinstance(node.func, ast.Attribute):
            callee = node.func.value

            if not (
                self.is_execute_like_name(callee)
                or self.is_cursor_call(callee)
                or self.is_connect_call(callee)
                or self.is_sqlite3_connect_call(callee)
            ):
                return

            if node.func.attr in SQLITE_EXECUTE_FUNCS:
                arg = node.args[0]

                if isinstance(arg, ast.Constant) and isinstance(
                    arg.value, str
                ):
                    error = util.validate(self.db_url, arg.value)

                    if error:
                        self.errors.append(SquallError(error, line=arg.lineno))

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            value = item.context_expr
            name = item.optional_vars

            if not (name and isinstance(name, ast.Name)):
                continue

            self.update_symbol_table(name.id, value)

        self.generic_visit(node)

    @property
    def db_url(self) -> str:
        return (
            str(self.settings.db)
            if self.settings and self.settings.db
            else ":memory:"
        )

    def is_connect_call(self, call: ast.AST) -> bool:
        return (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and self.symbols.get(call.func.id) == "sqlite3.connect"
        )

    def is_sqlite3_connect_call(self, call: ast.AST) -> bool:
        return (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and self.symbols.get(call.func.value.id) == "sqlite3"
            and call.func.attr == "connect"
        )

    def is_cursor_call(self, call: ast.AST) -> bool:
        return (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and self.symbols.get(call.func.value.id) == "sqlite3.Connection"
            and call.func.attr == "cursor"
        )

    def is_execute_like_name(self, name: ast.AST) -> bool:
        return (
            isinstance(name, ast.Name)
            and self.symbols.get(name.id) in SQL_EXECUTABLE_LIKE
        )

    def update_symbol_table(self, id: str, expr: ast.AST) -> None:
        if self.is_connect_call(expr) or self.is_sqlite3_connect_call(expr):
            ty = "sqlite3.Connection"

        elif self.is_cursor_call(expr):
            ty = "sqlite3.Cursor"

        else:
            return

        self.symbols[id] = ty
