import ast

from squall import util

SQLITE_EXECUTE_FUNCS = {"execute", "executescript", "executemany"}


# TODO: turn into a dataclass
SquallError = tuple[int, str]


class SqliteStmtVisitor(ast.NodeVisitor):
    symbols: dict[str, str]
    errors: list[SquallError]

    def __init__(self) -> None:
        self.symbols = {}
        self.errors = []

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.generic_visit(node)

        if node.module == "sqlite3":
            for name in node.names:
                if name.name == "connect":
                    self.symbols[name.asname or name.name] = "sqlite3.connect"

    def visit_Assign(self, node: ast.Assign) -> None:
        self.generic_visit(node)

        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and self.symbols.get(node.value.func.id) == "sqlite3.connect"
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
                    error = util.validate("db.db3", arg.value)

                    if error:
                        self.errors.append((arg.lineno, error))
