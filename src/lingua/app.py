from pathlib import Path

from flask import Flask, render_template

import src.lingua.events as events
import src.lingua.modules as modules
from src.lingua.content import ContentStore

ROOT = Path(__file__).parent


def create_app(content_dir=ROOT / "content"):
    app = Flask(__name__)
    app.config["DATA_DIR"] = ROOT / "data"
    store = ContentStore(content_dir)
    app.extensions["store"] = store

    app.register_blueprint(events.bp)
    for m in modules.REGISTRY:  # every learning module plugs in here
        app.register_blueprint(m.bp)

    @app.context_processor
    def inject_nav():
        return {"modules": modules.REGISTRY}

    @app.get("/")
    def home():
        counts = {m.TYPE: len(store.all(m.TYPE)) for m in modules.REGISTRY}
        return render_template("home.html", counts=counts, errors=store.errors)

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
