"""
Keskitetty asetusmoduuli.

Kaikki ympäristöstä riippuvat arvot (portit, tiedostopolut, admin-tunnus)
kootaan tähän yhteen paikkaan, jotta loppukoodi ei sekoile os.environ-kutsuilla.
"""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

STATIC_DIR = BASE_DIR / "static"
QUESTIONS_FILE = Path(__file__).resolve().parent / "questions.json"

DB_PATH = DATA_DIR / "vibe.db"
ADMIN_SECRET_FILE = DATA_DIR / "admin_secret.txt"


def _load_or_create_admin_token() -> str:
    """
    Admin-URL:n salainen tunnus. Voidaan asettaa ADMIN_TOKEN-ympäristömuuttujalla,
    muuten se generoidaan kerran ja tallennetaan levylle, jotta se pysyy samana
    palvelimen uudelleenkäynnistysten välillä (koko viikonlopun ajan).
    """
    env_token = os.environ.get("ADMIN_TOKEN")
    if env_token:
        return env_token
    if ADMIN_SECRET_FILE.exists():
        existing = ADMIN_SECRET_FILE.read_text().strip()
        if existing:
            return existing
    token = secrets.token_urlsafe(12)
    ADMIN_SECRET_FILE.write_text(token)
    return token


ADMIN_TOKEN = _load_or_create_admin_token()

# Kuinka moneen joukkueeseen osallistujat jaetaan.
TEAM_COUNT = int(os.environ.get("TEAM_COUNT", "4"))

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))
