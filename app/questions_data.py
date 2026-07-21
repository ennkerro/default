"""
Kysymyspankki - tallennettu tietokantaan, jotta admin voi muokata kysymyksia
selaimen kautta ilman koodin tai questions.json-tiedoston muokkaamista.

Ensimmaisella kaynnistyskerralla (kun tietokannassa ei viela ole yhtaan
kysymysta) pankki alustetaan questions.json-tiedoston oletussisallosta.
Sen jalkeen tietokanta on totuuden lahde - questions.json toimii vain
alkuperaisena "tehdasasetuksena" ja palautuspisteena.
"""
import json
import re
import uuid

from app import database
from app.config import QUESTIONS_FILE


def _load_defaults() -> list[dict]:
    with open(QUESTIONS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data["questions"]


def load_questions() -> list[dict]:
    existing = database.get_question_bank()
    if existing is not None:
        return existing
    defaults = _load_defaults()
    database.save_question_bank(defaults)
    return defaults


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


def reset_to_defaults() -> list[dict]:
    """Palauttaa kysymyspankin alkuperaisiin questions.json-oletuksiin."""
    defaults = _load_defaults()
    database.save_question_bank(defaults)
    return defaults


def auto_tag(text: str) -> str:
    """Yksinkertainen automaattinen tunnussana nimigeneraattoria varten, jos admin ei kirjoita omaa."""
    first_word = re.split(r"[\s,.\-–—:;!?()]+", text.strip())[0] if text.strip() else ""
    slug = re.sub(r"[^a-zA-ZäöåÄÖÅ]", "", first_word).lower()
    return slug or "vibe"


def normalize_questions(raw_questions: list[dict]) -> list[dict]:
    """
    Siistii ja validoi admin-kayttoliittymasta saapuvan kysymyslistan:
    - jokaisella kysymyksella pitaa olla teksti ja tasan 4 ei-tyhjaa vaihtoehtoa
    - puuttuva/tyhja id generoidaan kysymystekstista (uniikkina)
    - puuttuva/tyhja tag paatellaan automaattisesti option-tekstista
    - vibe_line saa olla tyhja - olemassaoleva varajarjestelma hoitaa sen
    Nostaa ValueErrorin jos data ei kelpaa.
    """
    if not raw_questions:
        raise ValueError("Kysymyspankissa pitää olla vähintään yksi kysymys.")

    used_ids: set[str] = set()
    normalized = []
    for i, q in enumerate(raw_questions):
        text = (q.get("text") or "").strip()
        if not text:
            raise ValueError(f"Kysymykseltä {i + 1} puuttuu teksti.")

        raw_options = q.get("options") or []
        if len(raw_options) != 4:
            raise ValueError(f'Kysymyksellä "{text}" pitää olla tasan 4 vaihtoehtoa.')

        options = []
        for opt in raw_options:
            opt_text = (opt.get("text") or "").strip()
            if not opt_text:
                raise ValueError(f'Kysymyksellä "{text}" on tyhjä vaihtoehto.')
            tag = (opt.get("tag") or "").strip() or auto_tag(opt_text)
            vibe_line = (opt.get("vibe_line") or "").strip() or None
            options.append({"text": opt_text, "tag": tag, "vibe_line": vibe_line})

        qid = (q.get("id") or "").strip()
        if not qid:
            base = re.sub(r"[^a-z0-9-]", "", text.lower().replace(" ", "-"))[:40] or "kysymys"
            qid = base
        while qid in used_ids:
            qid = f"{qid}-{uuid.uuid4().hex[:4]}"
        used_ids.add(qid)

        normalized.append({"id": qid, "text": text, "options": options})

    return normalized
