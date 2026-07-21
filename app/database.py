"""
Pieni SQLite-kerros. Ei ORM:ia - taman kokoluokan sovellukselle (8-15
osallistujaa kerrallaan) raaka SQL on yksinkertaisin ja luotettavin ratkaisu.

Jokainen funktio avaa oman lyhytikaisen yhteyden. SQLiten WAL-tila sallii
samanaikaiset luvut kirjoitusten aikana, ja kirjoitukset suojataan lockilla
etta kaksi pyyntoa ei koskaan kirjoita paallekkain.
"""
import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

from app.config import DB_PATH

_write_lock = threading.Lock()


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS answers (
                participant_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                option_index INTEGER NOT NULL,
                PRIMARY KEY (participant_id, question_id),
                FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                teams_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        conn.commit()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_participant(token: str, name: str) -> int:
    with _write_lock, _connect() as conn:
        cur = conn.execute(
            "INSERT INTO participants (token, name, created_at) VALUES (?, ?, ?)",
            (token, name.strip(), _now()),
        )
        conn.commit()
        return cur.lastrowid


def get_participant_by_token(token: str) -> Optional[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM participants WHERE token = ?", (token,)
        ).fetchone()


def get_all_participants() -> list[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM participants ORDER BY created_at ASC"
        ).fetchall()


def save_answers(participant_id: int, answers: dict[str, int]) -> None:
    with _write_lock, _connect() as conn:
        conn.executemany(
            """
            INSERT INTO answers (participant_id, question_id, option_index)
            VALUES (?, ?, ?)
            ON CONFLICT(participant_id, question_id)
            DO UPDATE SET option_index = excluded.option_index
            """,
            [(participant_id, qid, idx) for qid, idx in answers.items()],
        )
        conn.execute(
            "UPDATE participants SET completed_at = ? WHERE id = ?",
            (_now(), participant_id),
        )
        conn.commit()


def get_answers_for_participant(participant_id: int) -> dict[str, int]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT question_id, option_index FROM answers WHERE participant_id = ?",
            (participant_id,),
        ).fetchall()
        return {row["question_id"]: row["option_index"] for row in rows}


def get_all_answers() -> dict[int, dict[str, int]]:
    """Palauttaa {participant_id: {question_id: option_index}} kaikille vastanneille."""
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM answers").fetchall()
    result: dict[int, dict[str, int]] = {}
    for row in rows:
        result.setdefault(row["participant_id"], {})[row["question_id"]] = row["option_index"]
    return result


def save_results(teams: list[dict]) -> None:
    with _write_lock, _connect() as conn:
        conn.execute(
            """
            INSERT INTO results (id, teams_json, created_at) VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET teams_json = excluded.teams_json, created_at = excluded.created_at
            """,
            (json.dumps(teams), _now()),
        )
        conn.commit()


def get_results() -> Optional[list[dict]]:
    with _connect() as conn:
        row = conn.execute("SELECT teams_json FROM results WHERE id = 1").fetchone()
        return json.loads(row["teams_json"]) if row else None


def get_results_version() -> Optional[str]:
    """
    Aikaleima siita milloin joukkueet viimeksi muodostettiin. Kasvaa joka
    kerta kun admin painaa nappia uudelleen (esim. joku vastasi myohassa),
    jotta asiakkaat huomaavat tuloksen vaihtuneen eivatka vain tuijota
    ensimmaista, jo vanhentunutta paljastusta.
    """
    with _connect() as conn:
        row = conn.execute("SELECT created_at FROM results WHERE id = 1").fetchone()
        return row["created_at"] if row else None


def reset_all() -> None:
    """Tyhjentaa koko tilan - kayttokelpoinen kun sovellusta kaytetaan uudelleen seuraavana viikonloppuna."""
    with _write_lock, _connect() as conn:
        conn.executescript(
            """
            DELETE FROM answers;
            DELETE FROM participants;
            DELETE FROM results;
            """
        )
        conn.commit()
