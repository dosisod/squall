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

static const char *validate_stmt(const char *db_url, const char *stmt) {
	sqlite3 *db = NULL;

	int err = sqlite3_open_v2(db_url, &db, SQLITE_OPEN_READONLY, NULL);
	if (err) return sqlite3_errmsg(db);

	sqlite3_stmt *prepared_stmt = NULL;
	const char *unused_sql = NULL;

	for (;;) {
		err = sqlite3_prepare_v2(db, stmt, strlen(stmt), &prepared_stmt, &unused_sql);
		if (err) return sqlite3_errmsg(db);

		for (;;) {
			err = sqlite3_step(prepared_stmt);

			const char *error_msg = sqlite3_errmsg(db);

			if (
				err == SQLITE_ROW ||
				err == SQLITE_DONE ||
				err == SQLITE_READONLY
			) break;

			if (error_msg) {
				sqlite3_finalize(prepared_stmt);
				return error_msg;
			}
		}

		sqlite3_finalize(prepared_stmt);

		if (!unused_sql || !*unused_sql) break;

		stmt = unused_sql;
	}

	return NULL;
}

PyObject *util_validate(PyObject *self, PyObject *args) {
	const char *db_url;
	const char *stmt;

	if (!PyArg_ParseTuple(args, "ss", &db_url, &stmt)) {
		return NULL;
	}

	const char *err = validate_stmt(db_url, stmt);

	if (err) return PyUnicode_FromString(err);

	Py_INCREF(Py_None);
	return Py_None;
}
