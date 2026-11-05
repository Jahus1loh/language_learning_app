from pathlib import Path


def read_account_exists():
    with (
        Path(__file__).parent.joinpath("sql_queries", "account_exists.sql").open() as f
    ):
        sql = f.read()
    return sql


def read_insert_user():
    with Path(__file__).parent.joinpath("sql_queries", "insert_user.sql").open() as f:
        sql = (
            f.read()
        )
    return sql


def read_select_user():
    with Path(__file__).parent.joinpath("sql_queries", "select_user.sql").open() as f:
        sql = f.read()
    return sql


def read_select_user_by_id():
    with Path(__file__).parent.joinpath(
        "sql_queries", "select_user_by_id.sql"
    ).open() as f:
        sql = f.read()
    return sql