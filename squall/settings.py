from __future__ import annotations

from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    files: list[Path]
    db: Path | None = None

    @classmethod
    def from_args(cls, *args: str) -> Settings:
        namespace = parse_args(*args)

        return cls(
            files=[Path(x) for x in namespace.files],
            db=Path(namespace.db) if namespace.db else None,
        )


def parse_args(*args: str) -> Namespace:
    parser = ArgumentParser()

    parser.add_argument("files", nargs="+")
    parser.add_argument("--db")

    return parser.parse_args(args or None)
