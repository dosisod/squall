import sqlite3
import sqlite3 as sqlite3_alias
from sqlite3 import connect
from sqlite3 import connect as connect_alias

# test connection via `connect()` is tracked
db = connect("db.db3")
db.execute("SELECT FROM users;")


# test connection via `connect()` via alias is tracked
db2 = connect_alias("db.db3")
db2.execute("SELECT FROM users;")


# test connection via `sqlite3.connect()` is tracked
db3 = sqlite3.connect("db.db3")
db3.execute("SELECT invalid_sql;")

# test connection via `sqlite3.connect()` imported as an alias is tracked
db4 = sqlite3_alias.connect("db.db3")
db4.execute("SELECT invalid_sql;")


# test execution via cursor (from assignment)
cursor = db.cursor()
cursor.execute("SELECT invalid_sql;")

# test execution via cursor (directly on connection)
db.cursor().execute("SELECT invalid_sql;")


# test execution directly on connection is tracked
connect("db.db3").execute("SELECT invalid_sql;")

# test execution directly on connection (via sqlite3 import) is tracked
sqlite3.connect("db.db3").execute("SELECT invalid_sql;")


# test execution via context manager
with connect(":memory:") as db:
    db.execute("SELECT invalid_sql;")


# test execution via function return value
def f_annotated() -> sqlite3.Connection:  # type: ignore
    # if there is a return type annotation, trust it.
    pass

f_annotated().execute("SELECT invalid_sql;")


# test execution via function return value (using string type annotation)
def f_str_annotated() -> "sqlite3.Connection":  # type: ignore
    pass

f_str_annotated().execute("SELECT invalid_sql;")


# test execution via typed argument
def f_params(
    # test non-kwarg with normal annotation
    db: sqlite3.Connection,
    *,
    # test kwarg with string annotation
    db2: "sqlite3.Connection"
) -> None:
    db.execute("SELECT invalid_sql;")
    db2.execute("SELECT invalid_sql;")


# test execution via class fields
class C:
    db: sqlite3.Connection
    db2: "sqlite3.Connection"

    def f(self) -> None:
        self.db.execute("SELECT invalid_sql")

    @classmethod
    def f2(cls) -> None:
        cls.db.execute("SELECT invalid_sql")

C().db.execute("SELECT invalid_sql")
C().db2.execute("SELECT invalid_sql")


# ensure multiple statements are checked if they exist
db.executescript("SELECT 1; SELECT invalid_sql")


# disallow multiple statements unless you're using executescript()
db.execute("SELECT 1; SELECT 2")
db.executemany("SELECT 1; SELECT 2", [])


# disallow mismatched number of query params and passed params
db.execute("SELECT 1", [1])
db.execute("SELECT ?")
db.execute("SELECT ?", [])
db.execute("SELECT ?, ?", [])
db.execute("SELECT ?, ?", [1])
db.execute("SELECT ?", [1, 2])
db.execute("SELECT ?", (1, 2))
