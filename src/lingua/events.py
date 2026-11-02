"""Learning-event log. Today it just appends JSON lines to data/events.jsonl.
Later the camera/fatigue module can send its scores here too."""
import json
import time
from pathlib import Path

from flask import Blueprint, current_app, request

bp = Blueprint("events", __name__, url_prefix="/api")


def record(kind, **data):
    folder = Path(current_app.config["DATA_DIR"])
    folder.mkdir(exist_ok=True)
    with open(folder / "events.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({**data, "t": time.time(), "kind": kind}) + "\n")


@bp.post("/events")
def post_event():
    body = request.get_json(silent=True) or {}
    record(str(body.pop("kind", "unknown")), **body)
    return "", 204
