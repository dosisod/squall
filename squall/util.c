#define Py_LIMITED_API 0x03080000
#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <sqlite3.h>

#if __GNUC__ || __clang__
#define UNUSED __attribute__((unused))
#else
#define UNUSED
#endif

PyObject *util_validate(PyObject *self, PyObject *args, PyObject *kwargs);

static PyMethodDef util_methods[] = {
	{"validate", _PyCFunction_CAST(util_validate), METH_VARARGS | METH_KEYWORDS, NULL},
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

static PyObject *validate_stmt(
	const char *db_url,
	const char *stmt,
	ExecutionType exec_type,
	int query_param_count
) {
	sqlite3 *db = NULL;

	int err = sqlite3_open_v2(db_url, &db, SQLITE_OPEN_READONLY, NULL);
	if (err) return PyUnicode_FromString(sqlite3_errmsg(db));

	sqlite3_stmt *prepared_stmt = NULL;
	const char *unused_sql = NULL;
	int stmt_count = 0;

	for (;;) {
		err = sqlite3_prepare_v2(db, stmt, strlen(stmt), &prepared_stmt, &unused_sql);
		if (err) return PyUnicode_FromString(sqlite3_errmsg(db));

		if (!prepared_stmt) {
			if (stmt_count == 0) {
				return PyUnicode_FromString("No SQL statement found");
			}

			// whitespace after a statement, no harm
			Py_INCREF(Py_None);
			return Py_None;
		}

		if (stmt_count > 0 && (exec_type == SQUALL_EXECUTE || exec_type == SQUALL_EXECUTEMANY)) {
			return PyUnicode_FromFormat(
				"Cannot use multiple SQL statements with `%s`",
				exec_type == SQUALL_EXECUTE ? "execute" : "executemany"
			);
		}

		if (query_param_count != -1) {
			// only check number of args in query if we know number of query parameters
			int param_count = sqlite3_bind_parameter_count(prepared_stmt);

			if (param_count != query_param_count) {
				return PyUnicode_FromFormat(
					"Expected %i query parameters, got %i instead",
					param_count,
					query_param_count
				);
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
				return PyUnicode_FromString(sqlite3_errmsg(db));
			}
		}

		sqlite3_finalize(prepared_stmt);

		if (!unused_sql || !*unused_sql) break;

		stmt = unused_sql;
		stmt_count++;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

PyObject *util_validate(UNUSED PyObject *self, PyObject *args, PyObject *kwargs) {
	const char *db_url;
	const char *stmt;
	const char *exec_func_name = NULL;
	ExecutionType exec_type = SQUALL_QUERY;
	int query_param_count = -1;

	static char *kwarg_names[] = {"db_url", "stmt", "exec_func", "query_param_count", NULL};

	if (!PyArg_ParseTupleAndKeywords(args, kwargs, "ss|si", kwarg_names, &db_url, &stmt, &exec_func_name, &query_param_count)) {
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

	return validate_stmt(db_url, stmt, exec_type, query_param_count);
}
