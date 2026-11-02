import pytest
from src.lingua.app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app()
    app.config.update(TESTING=True, DATA_DIR=tmp_path)
    return app.test_client()


def test_pages_load(client):
    for url in ["/", "/flashcards/", "/flashcards/food-a2", "/reading/", "/reading/market-b1"]:
        assert client.get(url).status_code == 200


def test_reading_scores_answers(client):
    r = client.post("/reading/market-b1", data={"q1": 1, "q2": 2, "q3": 0})
    assert b"3 of 3" in r.data


def test_unknown_lesson_is_404(client):
    assert client.get("/reading/nope").status_code == 404
