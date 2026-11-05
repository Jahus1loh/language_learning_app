import mysql.connector
from werkzeug.security import generate_password_hash

from src.lingua.config.config import Config
from src.lingua.database.read_queries import (
    read_account_exists,
    read_insert_user,
    read_select_user,
    read_select_user_by_id,
)

from .db import get_db


class AccountExistsError(Exception):
    """The username or email is already taken."""


def account_exists(username, email):
    with get_db().cursor(prepared=True) as cursor:
        cursor.execute(
            read_account_exists(),
            (username, email),
        )
        return cursor.fetchone() is not None


def _hash(password):
    return generate_password_hash(password, method=Config.PASSWORD_HASH_METHOD)


def _insert(username, email, hashed_password):
    with get_db().cursor(prepared=True) as cursor:
        cursor.execute(read_insert_user(), (username, email, hashed_password))
    get_db().commit()


def create_account(username, email, password):
    try:
        _insert(username, email, _hash(password))
    except mysql.connector.IntegrityError as e:
        raise AccountExistsError from e


def get_account(username):
    """Return the account as a dict, or None if no account matches."""
    with get_db().cursor(prepared=True, dictionary=True) as cursor:
        cursor.execute(read_select_user(), (username,))
        return cursor.fetchone()


def get_account_by_id(account_id):
    with get_db().cursor(prepared=True, dictionary=True) as cursor:
        cursor.execute(
            read_select_user_by_id(),
            (account_id,),
        )
        return cursor.fetchone()
