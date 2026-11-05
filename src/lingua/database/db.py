import mysql.connector
from flask import current_app, g


def get_db():
    if "db" not in g:
        db_config = current_app.config["DB_CONFIG"]
        g.db = mysql.connector.connect(**db_config)

    return g.db


def test_db():
    db = get_db()

    print("DB connected:", db.is_connected())
    print("DB host:", db.server_host)
    print("DB port:", db.server_port)

    with db.cursor() as cursor:
        cursor.execute("SELECT DATABASE(), VERSION()")
        print("DB info:", cursor.fetchone())


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    app.teardown_appcontext(close_db)
