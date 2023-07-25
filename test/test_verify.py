from pathlib import Path

from squall.main import get_sqlite_errors_from_code
from squall.util import validate
from squall.visitor import SquallError


def test_normal_code_doesnt_emit_sqlite_errors() -> None:
    code = """\
class DB:
    def execute(self, sql: str) -> None:
        pass

db = DB()

# should not emit since db is of type DB, not sqlite3.Connection
db.execute("")


# normal assignment, dont do anything
x = 1
"""

    assert not get_sqlite_errors_from_code(code)


def test_verify_invalid_sql() -> None:
    code = (Path(__file__).parent / "data" / "verify.py").read_text()

    errors = get_sqlite_errors_from_code(code)

    assert errors == [
        SquallError(error='near "FROM": syntax error', line=8),
        SquallError(error='near "FROM": syntax error', line=13),
        SquallError(error="no such column: invalid_sql", line=18),
        SquallError(error="no such column: invalid_sql", line=22),
        SquallError(error="no such column: invalid_sql", line=27),
        SquallError(error="no such column: invalid_sql", line=30),
        SquallError(error="no such column: invalid_sql", line=34),
        SquallError(error="no such column: invalid_sql", line=37),
    ]


def test_empty_sql_is_invalid() -> None:
    assert validate(":memory:", "") == "No SQL statement found"
