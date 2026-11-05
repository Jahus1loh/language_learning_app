from flask import Blueprint, current_app, render_template

from src.lingua import modules
from src.lingua.validators import login_required

bp = Blueprint("main", __name__)


@bp.context_processor
def inject_nav():
    return {"modules": modules.REGISTRY}


@bp.get("/home")
def home():
    store = current_app.extensions["store"]

    counts = {module.TYPE: len(store.all(module.TYPE)) for module in modules.REGISTRY}

    return render_template(
        "home.html",
        counts=counts,
        errors=store.errors,
    )
