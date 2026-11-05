from flask import Blueprint, abort, render_template, request

from src.lingua import events
from src.lingua.content import store
from src.lingua.validators import login_required

TITLE, TYPE = "Reading", "reading"
BLURB = "Read a short text and answer questions."
bp = Blueprint("reading", __name__, url_prefix="/reading")


@bp.get("/")
@login_required
def index():
    return render_template("lessons.html", title=TITLE, endpoint="reading.lesson",
                           lessons=store().all(TYPE))


@bp.route("/<lesson_id>", methods=["GET", "POST"])
@login_required
def lesson(lesson_id):
    text = store().get(TYPE, lesson_id) or abort(404)
    result = None
    if request.method == "POST":
        picks = {q["id"]: request.form.get(q["id"], type=int) for q in text["questions"]}
        score = sum(picks[q["id"]] == q["answer"] for q in text["questions"])
        result = {"picks": picks, "score": score}
        events.record("reading_submitted", lesson=lesson_id, score=score,
                      total=len(text["questions"]))
    return render_template("reading.html", text=text, result=result)
