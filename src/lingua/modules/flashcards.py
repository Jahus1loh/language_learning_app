from flask import Blueprint, abort, render_template

from src.lingua.content import store

TITLE, TYPE = "Flashcards", "vocabulary"
BLURB = "Learn new words with two-sided cards."
bp = Blueprint("flashcards", __name__, url_prefix="/flashcards")


@bp.get("/")
def index():
    return render_template("lessons.html", title=TITLE, endpoint="flashcards.lesson",
                           lessons=store().all(TYPE))


@bp.get("/<lesson_id>")
def lesson(lesson_id):
    deck = store().get(TYPE, lesson_id) or abort(404)
    return render_template("flashcards.html", deck=deck)
