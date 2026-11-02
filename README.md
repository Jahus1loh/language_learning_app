# Lingua – sprint 1

Flask app with a vocabulary flashcard module and a reading module. Lessons are JSON files in `content/`.

## Run
    python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    flask --app app run --debug        # http://127.0.0.1:5000
    pytest

## Layout
- `app.py` – app factory; registers every module in `modules.REGISTRY`
- `content.py` – loads and validates lesson JSON; bad files are skipped and listed on the home page
- `modules/` – one file per learning module (blueprint + TITLE, TYPE, BLURB)
- `events.py` – `POST /api/events` and `record()` write to `data/events.jsonl` (answer times, scores). The future fatigue module will use this.

## JSON format (agree on it with whoever writes the tasks)
Vocabulary: `{"type":"vocabulary","id":"...","title":"...","level":"A2","cards":[{"id","front","back","example"?}]}`
Reading: `{"type":"reading","id":"...","title":"...","level":"B1","text":"paragraphs separated by a blank line","questions":[{"id","prompt","options":[...],"answer":<index of correct option>}]}`

## Add a module
Create `modules/<name>.py` with `TITLE`, `TYPE`, `BLURB`, `bp`; add its item schema to `SCHEMA` in `content.py`; add it to `REGISTRY`.
