from flask import request


def add_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"

    if request.endpoint != "static":
        response.headers["Cache-Control"] = "no-store"

    return response


def init_security(app):
    app.after_request(add_security_headers)