from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from src.lingua.validators import login_required, validate_registration

from ..database.accounts import (
    AccountExistsError,
    account_exists,
    create_account,
    get_account,
    get_account_by_id,
)
from ..extensions import limiter

bp = Blueprint("auth", __name__)

REGISTER_FIELDS = ("username", "email", "password")
LOGIN_FIELDS = ("username", "password")
EXISTS_MSG = "An account with that username or email already exists!"
SUCCESS_MSG = "You have successfully registered! You can now log in."
BAD_LOGIN_MSG = "Incorrect username or password!"


def _show_login(msg=""):
    return render_template("index.html", msg=msg)


def _fields(form):
    """Return (username, password), or None if a field is missing."""
    if not all(key in form for key in LOGIN_FIELDS):
        return None
    return form["username"].strip(), form["password"]


def _authenticate(username, password):
    """Return the account if the credentials match, else None."""
    account = get_account(username)
    if account and check_password_hash(account["password"], password):
        return account
    return None


def _start_session(account):
    session.clear()
    session["loggedin"] = True
    session["id"] = account["id"]
    session["username"] = account["username"]


def _login_post():
    fields = _fields(request.form)
    account = fields and _authenticate(*fields)
    if not account:
        return _show_login(BAD_LOGIN_MSG if fields else "")
    _start_session(account)
    return redirect(url_for("main.home"))


@bp.route("/", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if "loggedin" in session:
        return redirect(url_for("main.index"))
    if request.method == "POST":
        return _login_post()
    return _show_login()


def _show_form(msg=""):
    return render_template("register.html", msg=msg)


def _read_form(form):
    """Return (username, email, password), or None if a field is missing."""
    if not all(key in form for key in REGISTER_FIELDS):
        return None
    return form["username"].strip(), form["email"].strip(), form["password"]


def _check(username, email, password):
    """Return an error message if the data can't be used, else ''."""
    error = validate_registration(username, email, password)
    if not error and account_exists(username, email):
        error = EXISTS_MSG
    return error or ""


def _create(username, email, password):
    try:
        create_account(username, email, password)
    except AccountExistsError:
        return EXISTS_MSG
    return ""


def _register_error(username, email, password):
    """Return an error message, or '' if the account was created."""
    error = _check(username, email, password)
    return error or _create(username, email, password)


def _process_form(form):
    """Return an error message, or '' if the account was created."""
    fields = _read_form(form)
    if fields is None:
        return "Please fill out the form!"
    return _register_error(*fields)


def _register_post():
    msg = _process_form(request.form)
    if msg:
        return _show_form(msg)
    flash(SUCCESS_MSG)
    return redirect(url_for("auth.login"))


@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def register():
    if "loggedin" in session:
        return redirect(url_for("main.home"))
    if request.method == "POST":
        return _register_post()
    return _show_form()


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("auth.login"))


@bp.route("/profile")
@login_required
def profile():
    account = get_account_by_id(session["id"])
    if account is None:
        session.clear()
        return redirect(url_for("login"))
    return render_template("profile.html", account=account)
