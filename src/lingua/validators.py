import re

USERNAME_RE = re.compile(r'[A-Za-z0-9]{3,20}')
EMAIL_RE = re.compile(r'[^@\s]+@[^@\s]+\.[^@\s]+')


def _username_error(username):
    if not USERNAME_RE.fullmatch(username):
        return 'Username must be 3 to 20 letters and numbers!'
    return None


def _email_error(email):
    if len(email) > 100 or not EMAIL_RE.fullmatch(email):
        return 'Please enter a valid email address!'
    return None


def _password_error(password):
    if not 8 <= len(password) <= 128:
        return 'Password must be 8 to 128 characters long!'
    return None


def validate_registration(username, email, password):
    """Return the first error message, or None if the data is valid."""
    errors = (_username_error(username), _email_error(email),
              _password_error(password))
    return next((e for e in errors if e), None)