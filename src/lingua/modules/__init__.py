"""A learning module = a file with TITLE, TYPE (lesson type in the JSON),
BLURB and a Flask blueprint `bp`. Add it to REGISTRY and it appears in the app."""
from src.lingua.modules import flashcards, reading

REGISTRY = [flashcards, reading]
