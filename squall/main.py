import ast
import sys
from collections.abc import Iterator
from pathlib import Path

from squall.visitor import SqliteStmtVisitor, SquallError


def get_sqlite_errors_from_code(code: str) -> list[SquallError]:
    tree = ast.parse(code)

    visitor = SqliteStmtVisitor()
    visitor.visit(tree)

    return visitor.errors


def get_sqlite_errors_from_file(file: Path) -> list[SquallError]:
    code = file.read_text()

    return get_sqlite_errors_from_code(code)


def main(files: Iterator[Path]) -> None:
    had_error = False

    for file in files:
        for error in get_sqlite_errors_from_file(file):
            print(f"{file}:{error}")  # noqa: T201
            had_error = True

    if had_error:
        sys.exit(1)
