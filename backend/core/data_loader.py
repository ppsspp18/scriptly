import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename: str):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


plays = load_json("plays.json")
characters = load_json("characters.json")
scenes = load_json("scenes.json")
speeches = load_json("speeches.json")