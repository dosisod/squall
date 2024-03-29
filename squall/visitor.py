import ast
from dataclasses import dataclass
from typing import TypeGuard

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
        self.symbols = {
            "sqlite3.connect()": "sqlite3.Connection",
            "sqlite3.Connection.cursor()": "sqlite3.Cursor",
        }

        for symbol in SQL_EXECUTABLE_LIKE:
            self.symbols[symbol] = symbol

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

        if len(node.args) == 0:
            # execute() funcs require at least 1 arg, so bail early if this isnt the case
            return

        if isinstance(node.func, ast.Attribute):
            if self.get_symbol(node.func.value) not in SQL_EXECUTABLE_LIKE:
                return

            if node.func.attr in SQLITE_EXECUTE_FUNCS:
                query = node.args[0]

                if isinstance(query, ast.Constant) and isinstance(query.value, str):
                    query_param_count = self.get_query_param_count(node.args)

                    error = util.validate(
                        self.db_url,
                        query.value,
                        node.func.attr,
                        query_param_count,
                    )

                    if error:
                        self.errors.append(SquallError(error, line=query.lineno))

    def get_query_param_count(self, args: list[ast.expr]) -> int:
        arg_count = len(args)

        if arg_count == 1:
            return 0

        if arg_count == 2:
            query_params = args[1]

            if isinstance(query_params, ast.List | ast.Tuple):
                if any(isinstance(param, ast.Starred) for param in query_params.elts):
                    return -1

                return len(query_params.elts)

        return -1

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            value = item.context_expr
            name = item.optional_vars

            if not (name and isinstance(name, ast.Name)):
                continue

            self.update_symbol_table(name.id, value)

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.returns:
            if symbol := self.get_symbol(node.returns):
                self.symbols[f"{node.name}()"] = symbol

            elif self.is_sqlite3_string_annotation(node.returns):
                self.symbols[f"{node.name}()"] = node.returns.value

        for arg in node.args.args + node.args.kwonlyargs:
            if arg.annotation:
                if symbol := self.get_symbol(arg.annotation):
                    self.symbols[f"{arg.arg}"] = symbol

                elif self.is_sqlite3_string_annotation(arg.annotation):
                    self.symbols[f"{arg.arg}"] = arg.annotation.value

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for stmt in node.body:
            if not (isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)):
                continue

            name = f"{node.name}.{stmt.target.id}"

            if symbol := self.get_symbol(stmt.annotation):
                self.symbols[name] = symbol

            elif self.is_sqlite3_string_annotation(stmt.annotation):
                self.symbols[name] = stmt.annotation.value

            self.symbols[f"{node.name}()"] = node.name

        # TODO: don't assume self and cls are always a part of the class, even
        # though they most likely are.
        self.symbols["self"] = node.name
        self.symbols["cls"] = node.name

        self.generic_visit(node)

        del self.symbols["self"]
        del self.symbols["cls"]

    @property
    def db_url(self) -> str:
        return str(self.settings.db) if self.settings and self.settings.db else ":memory:"

    def is_sqlite3_string_annotation(self, const: ast.AST) -> TypeGuard[ast.Constant]:
        return isinstance(const, ast.Constant) and const.value in SQL_EXECUTABLE_LIKE

    def update_symbol_table(self, id: str, expr: ast.AST) -> None:
        if symbol := self.get_symbol(expr):
            self.symbols[id] = symbol

    def get_symbol(self, node: ast.AST) -> str | None:
        name = self.get_name(node)

        if "!" in name:
            return None

        return self.symbols.get(name)

    def get_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):
            name = self.get_name(node.value)
            name = self.symbols.get(name, name)
            return f"{name}.{node.attr}"

        if isinstance(node, ast.Call):
            name = self.get_name(node.func)
            name = self.symbols.get(name, name)
            return f"{name}()"

        # Poison value to cause symbol lookup to fail
        return "!"
