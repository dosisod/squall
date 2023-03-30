import ast
import sys
from pathlib import Path
from typing import Iterable

from squall.visitor import SqliteStmtVisitor


def main(files: Iterable[Path]) -> None:
    for file in files:
        tree = ast.parse(file.read_text())

        visitor = SqliteStmtVisitor()
        visitor.visit(tree)

        for line, error in visitor.errors:
            print(f"file.py:{line}: {error}")


if __name__ == "__main__":
    main(Path(x) for x in sys.argv[1:])
