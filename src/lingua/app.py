from flask import Flask

from src.lingua import events, modules
from src.lingua.config.config import Config
from src.lingua.content import ContentStore
from src.lingua.database.db import init_db, test_db
from src.lingua.extensions import init_extensions
from src.lingua.routes import auth, errors, main
from src.lingua.security import init_security


def create_app(content_dir=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    validate_config(app)

    init_extensions(app)
    init_db(app)
    init_security(app)

    store = ContentStore(content_dir or Config.ROOT / "content")

    app.extensions["store"] = store

    register_blueprints(app)

    return app


def validate_config(app):
    secret_key = app.config["SECRET_KEY"]

    if len(secret_key) < 32 or secret_key.startswith("replace-this"):
        raise SystemExit(
            "Set SECRET_KEY in the .env file to a long random string first!"
        )


def register_blueprints(app):
    app.register_blueprint(main.bp)
    app.register_blueprint(events.bp)
    app.register_blueprint(auth.bp)
    errors.register_error_handlers(app)

    for module in modules.REGISTRY:
        app.register_blueprint(module.bp)
