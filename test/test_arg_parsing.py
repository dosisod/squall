from pathlib import Path

from squall.settings import Settings


def test_basic_arg_parsing() -> None:
    settings = Settings.from_args(
        "file1.py",
        "file2.py",
        "--db",
        "db.db3",
    )

    assert settings == Settings(
        files=[Path("file1.py"), Path("file2.py")],
        db=Path("db.db3"),
    )


def test_parse_args_without_db_flag() -> None:
    settings = Settings.from_args(
        "file1.py",
        "file2.py",
    )

    assert settings == Settings(files=[Path("file1.py"), Path("file2.py")])
