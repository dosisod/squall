from pathlib import Path

from squall.main import get_sqlite_errors_from_code
from squall.util import validate
from squall.visitor import SquallError


def test_normal_code_doesnt_emit_sqlite_errors() -> None:
    code = """\
import sqlite3
from contextlib import nullcontext

class DB:
    def execute(self, sql: str) -> None:
        pass

db = DB()

# should not emit since db is of type DB, not sqlite3.Connection
db.execute("")


# normal assignment, dont do anything
x = 1


# empty context manager, do nothing
with nullcontext():
    pass


db = sqlite3.connect(":memory:")

# missing semicolon, existing semicolon, and whitespace after semicolon are ok
db.execute("SELECT 1")
db.execute("SELECT 1;")
db.execute("SELECT 1; ")

# ok to execute multiple statements with executescript()
db.executescript("SELECT 1; SELECT 2")


# ensure matching number of query param/passed params is allowed
db.execute("SELECT 1", [])
db.execute("SELECT 1", ())
db.execute("SELECT ?", [1])
db.execute("SELECT ?, ?", [1, 2])
db.execute("SELECT ?, ?", (1, 2))


# ignore param count when using star exprs
db.execute("SELECT 1", [*[1, 2, 3]])


# don't try to deduce param count for identifiers
args = [1]
db.execute("SELECT 1", args)


# silently ignore execute without sql statement as its a type error, not a squall error
db.execute()
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
        SquallError(error="no such column: invalid_sql", line=42),
        SquallError(error="no such column: invalid_sql", line=50),
        SquallError(error="no such column: invalid_sql", line=57),
        SquallError(error="no such column: invalid_sql", line=68),
        SquallError(error="no such column: invalid_sql", line=69),
        SquallError(error="no such column: invalid_sql", line=78),
        SquallError(error="no such column: invalid_sql", line=82),
        SquallError(error="no such column: invalid_sql", line=84),
        SquallError(error="no such column: invalid_sql", line=85),
        SquallError(error="no such column: invalid_sql", line=89),
        SquallError(error="Cannot use multiple SQL statements with `execute`", line=93),
        SquallError(error="Cannot use multiple SQL statements with `executemany`", line=94),
        SquallError(error="Expected 0 query parameters, got 1 instead", line=98),
        SquallError(error="Expected 1 query parameters, got 0 instead", line=99),
        SquallError(error="Expected 1 query parameters, got 0 instead", line=100),
        SquallError(error="Expected 2 query parameters, got 0 instead", line=101),
        SquallError(error="Expected 2 query parameters, got 1 instead", line=102),
        SquallError(error="Expected 1 query parameters, got 2 instead", line=103),
        SquallError(error="Expected 1 query parameters, got 2 instead", line=104),
    ]


def test_empty_sql_is_invalid() -> None:
    assert validate(":memory:", "") == "No SQL statement found"


def test_kwargs_are_allowed() -> None:
    err = validate(db_url=":memory:", stmt="", exec_func="execute", query_param_count=0)

    assert err == "No SQL statement found"
