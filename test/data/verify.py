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
