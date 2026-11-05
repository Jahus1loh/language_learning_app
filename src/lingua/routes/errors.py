from flask import redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFError

TEMPLATES = {"auth.register": "register.html", "auth.login": "index.html"}
MESSAGES = {429: "Too many attempts! Please wait a minute and try again."}
EXPIRED_MSG = "The form has expired! Please try again."


def _form_endpoint():
    """The endpoint of the form the visitor was using."""
    if request.endpoint == "auth.register":
        return "auth.register"
    return "auth.login"


def _redirect_target(endpoint):
    """URL to redirect to instead of showing the form, or None."""
    if not session:
        return url_for(endpoint)
    if "loggedin" in session:
        return url_for("main.home")
    return None


def _render_form(endpoint, error):
    msg = MESSAGES.get(error.code, EXPIRED_MSG)
    return render_template(TEMPLATES[endpoint], msg=msg), error.code


def form_error(error):
    endpoint = _form_endpoint()
    target = _redirect_target(endpoint)
    if target:
        return redirect(target)
    return _render_form(endpoint, error)


def register_error_handlers(app):
    app.register_error_handler(429, form_error)
    app.register_error_handler(CSRFError, form_error)
