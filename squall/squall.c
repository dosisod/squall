#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <sqlite3.h>

static PyObject *squall_validate(PyObject *self, PyObject *args);

static PyMethodDef squall_methods[] = {
    {"validate", squall_validate, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef squall_module = {
    PyModuleDef_HEAD_INIT,
    "squall",
    NULL,
    -1,
    squall_methods
};

PyMODINIT_FUNC PyInit_squall(void) {
    return PyModule_Create(&squall_module);
}

static const char *validate_stmt(const char *db_url, const char *stmt) {
	sqlite3 *db = NULL;

	int err = sqlite3_open_v2(db_url, &db, SQLITE_OPEN_READONLY, NULL);
	if (err) return sqlite3_errmsg(db);

	sqlite3_stmt *prepared_stmt = NULL;

	err = sqlite3_prepare_v2(db, stmt, strlen(stmt), &prepared_stmt, NULL);
	if (err) return sqlite3_errmsg(db);

	for (;;) {
		err = sqlite3_step(prepared_stmt);

		const char *error_msg = sqlite3_errmsg(db);

		if (err == SQLITE_ROW) continue;
		if (err == SQLITE_DONE) break;

		if (error_msg) {
			sqlite3_finalize(prepared_stmt);
			return error_msg;
		}
	}

	sqlite3_finalize(prepared_stmt);

	return NULL;
}

static PyObject *squall_validate(PyObject *self, PyObject *args) {
	const char *db_url;
	const char *stmt;

	if (!PyArg_ParseTuple(args, "ss", &db_url, &stmt)) {
		return NULL;
	}

	const char *err = validate(db_url, stmt);

	if (err) {
		// TODO: return string instead
		printf("squall: %s\n", err);
	}

	Py_INCREF(Py_None);
	return Py_None;
}
