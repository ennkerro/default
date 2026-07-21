"""Kysymyspankin lataus questions.json-tiedostosta (ladataan ja valimuistetaan kerran)."""
import json

from app.config import QUESTIONS_FILE

_cache: list[dict] | None = None


def load_questions() -> list[dict]:
    global _cache
    if _cache is None:
        with open(QUESTIONS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        _cache = data["questions"]
    return _cache


def question_ids() -> list[str]:
    return [q["id"] for q in load_questions()]


def public_questions() -> list[dict]:
    """Kysymykset asiakassovellukselle - ilman sisaista tag/vibe_line-metadataa."""
    return [
        {
            "id": q["id"],
            "text": q["text"],
            "options": [opt["text"] for opt in q["options"]],
        }
        for q in load_questions()
    ]
