#define Py_LIMITED_API 0x03080000
#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <sqlite3.h>

PyObject *util_validate(PyObject *self, PyObject *args);

static PyMethodDef util_methods[] = {
	{"validate", util_validate, METH_VARARGS, NULL},
	{NULL, NULL, 0, NULL}
};

static struct PyModuleDef util_module = {
	PyModuleDef_HEAD_INIT,
	"util",
	NULL,
	-1,
	util_methods
};

PyMODINIT_FUNC PyInit_util(void) {
	return PyModule_Create(&util_module);
}

typedef enum {
	SQUALL_QUERY,
	SQUALL_EXECUTE,
	SQUALL_EXECUTESCRIPT,
	SQUALL_EXECUTEMANY,
} ExecutionType;

static const char *validate_stmt(
	const char *db_url,
	const char *stmt,
	ExecutionType exec_type,
	int query_param_count
) {
	sqlite3 *db = NULL;

	int err = sqlite3_open_v2(db_url, &db, SQLITE_OPEN_READONLY, NULL);
	if (err) return sqlite3_errmsg(db);

	sqlite3_stmt *prepared_stmt = NULL;
	const char *unused_sql = NULL;
	int stmt_count = 0;

	for (;;) {
		err = sqlite3_prepare_v2(db, stmt, strlen(stmt), &prepared_stmt, &unused_sql);
		if (err) return sqlite3_errmsg(db);

		if (!prepared_stmt) {
			if (stmt_count == 0) {
				return "No SQL statement found";
			}

			// whitespace after a statement, no harm
			return NULL;
		}

		if (stmt_count > 0 && (exec_type == SQUALL_EXECUTE || exec_type == SQUALL_EXECUTEMANY)) {
			return "Cannot use multiple SQL statements with `execute` or `executemany`";
		}

		if (query_param_count != -1) {
			// only check number of args in query if we know number of query parameters
			int param_count = sqlite3_bind_parameter_count(prepared_stmt);

			if (param_count != query_param_count) {
				// TODO: add expected and received params to error message
				return "Mismatched number of args and query params";
			}
		}

		for (;;) {
			err = sqlite3_step(prepared_stmt);

			if (
				err == SQLITE_ROW ||
				err == SQLITE_DONE ||
				err == SQLITE_READONLY
			) break;

			if (err) {
				sqlite3_finalize(prepared_stmt);
				return sqlite3_errmsg(db);
			}
		}

		sqlite3_finalize(prepared_stmt);

		if (!unused_sql || !*unused_sql) break;

		stmt = unused_sql;
		stmt_count++;
	}

	return NULL;
}

PyObject *util_validate(PyObject *self, PyObject *args) {
	const char *db_url;
	const char *stmt;
	const char *exec_func_name = NULL;
	ExecutionType exec_type = SQUALL_QUERY;
	int query_param_count = -1;

	if (!PyArg_ParseTuple(args, "ss|si", &db_url, &stmt, &exec_func_name, &query_param_count)) {
		return NULL;
	}

	if (!exec_func_name) {
		// do nothing
	}
	else if (strcmp(exec_func_name, "execute") == 0) {
		exec_type = SQUALL_EXECUTE;
	}
	else if (strcmp(exec_func_name, "executemany") == 0) {
		exec_type = SQUALL_EXECUTEMANY;
	}
	else if (strcmp(exec_func_name, "executescript") == 0) {
		exec_type = SQUALL_EXECUTESCRIPT;
	}

	const char *err = validate_stmt(db_url, stmt, exec_type, query_param_count);

	if (err) return PyUnicode_FromString(err);

	Py_INCREF(Py_None);
	return Py_None;
}
