from squall.main import get_sqlite_errors_from_code
from squall.visitor import SquallError


def test_normal_code_doesnt_emit_sqlite_errors() -> None:
    code = """\
class DB:
    def execute(self, sql: str) -> None:
        pass

db = DB()

# should not emit, since db is of type DB, not sqlite3.Connection
db.execute("")
"""

    assert not get_sqlite_errors_from_code(code)


def test_verify_invalid_sql() -> None:
    code = """\
from sqlite3 import connect

db = connect("db.db3")

db.execute("SELECT FROM users;")
"""

    error, = get_sqlite_errors_from_code(code)

    assert error == SquallError('near "FROM": syntax error', line=5)
