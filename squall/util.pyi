def validate(
    db_url: str,
    stmt: str,
    exec_func: str | None = None,
    query_param_count: int = -1,
) -> str | None: ...
