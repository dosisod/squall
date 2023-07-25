import ast
import sys
from pathlib import Path

from squall.settings import Settings
from squall.visitor import SqliteStmtVisitor, SquallError


def get_sqlite_errors_from_code(
    code: str,
    settings: Settings | None = None,
) -> list[SquallError]:
    tree = ast.parse(code)

    if settings and settings.debug:
        print(ast.dump(tree, indent=2))  # noqa: T201

    visitor = SqliteStmtVisitor(settings)
    visitor.visit(tree)

    return visitor.errors


def get_sqlite_errors_from_file(
    file: Path,
    settings: Settings,
) -> list[SquallError]:
    code = file.read_text()

    return get_sqlite_errors_from_code(code, settings)


def main(settings: Settings) -> None:
    had_error = False

    for file in settings.files:
        for error in get_sqlite_errors_from_file(file, settings):
            print(f"{file}:{error}")  # noqa: T201
            had_error = True

    if had_error:
        sys.exit(1)
