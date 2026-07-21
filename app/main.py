"""
Kukonharjun Psykologinen Vibe-analyysi - FastAPI-sovellus.

Reititys:
  GET  /                          osallistujan yhden sivun sovellus
  GET  /admin/{secret}            admin-paneeli (vaatii oikean salaisuuden)
  GET  /api/questions             kysymyspankki asiakkaalle
  POST /api/register              uusi osallistuja {name} -> {token, id, name}
  GET  /api/me/{token}            osallistujan oma tila (sivun paivitysta varten)
  POST /api/submit                vastausten tallennus {token, answers}
  GET  /api/state                 koko tapahtuman nykytila (sama muoto kuin WS-viestit)
  POST /api/admin/{secret}/form-teams   muodosta joukkueet
  POST /api/admin/{secret}/reset        nollaa koko tapahtuma
  GET  /api/admin/{secret}/qr           QR-koodi osallistumisosoitteeseen (PNG)
  GET  /api/admin/{secret}/questions            kysymyspankki muokkausta varten
  PUT  /api/admin/{secret}/questions            tallenna muokattu kysymyspankki
  POST /api/admin/{secret}/questions/reset-defaults   palauta alkuperaiset kysymykset
  WS   /ws                        reaaliaikaiset tilapaivitykset kaikille
"""
import io
import json
import secrets
from contextlib import asynccontextmanager

import qrcode
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app import database
from app.clustering import form_teams
from app.config import ADMIN_TOKEN, STATIC_DIR, TEAM_COUNT
from app.models import (
    FormTeamsRequest,
    QuestionsUpdateRequest,
    RegisterRequest,
    RegisterResponse,
    SubmitRequest,
)
from app.questions_data import (
    load_questions,
    normalize_questions,
    public_questions,
    question_ids,
    reset_to_defaults,
)
from app.team_generator import generate_teams
from app.ws_manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="Kukonharjun Psykologinen Vibe-analyysi", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _check_admin(secret: str) -> None:
    # 404 eika 403, jotta vaaralla salaisuudella ei voi paatella etta reitti edes on olemassa.
    if not secrets.compare_digest(secret, ADMIN_TOKEN):
        raise HTTPException(status_code=404)


def _current_state() -> dict:
    participants = database.get_all_participants()
    teams = database.get_results()
    return {
        "type": "state",
        "total": len(participants),
        "completed": sum(1 for p in participants if p["completed_at"]),
        "teams_ready": teams is not None,
        "teams": teams,
        "teams_version": database.get_results_version(),
        "participants": [
            {"name": p["name"], "completed": bool(p["completed_at"])} for p in participants
        ],
    }


async def _broadcast_state() -> None:
    await manager.broadcast(_current_state())


# ---------------------------------------------------------------------------
# Sivut
# ---------------------------------------------------------------------------


@app.get("/")
async def index_page():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/admin/{secret}")
async def admin_page(secret: str):
    _check_admin(secret)
    return FileResponse(str(STATIC_DIR / "admin.html"))


# ---------------------------------------------------------------------------
# Julkinen API
# ---------------------------------------------------------------------------


@app.get("/api/questions")
async def get_questions():
    return public_questions()


@app.get("/api/state")
async def get_state():
    return _current_state()


@app.post("/api/register", response_model=RegisterResponse)
async def register(payload: RegisterRequest):
    token = secrets.token_urlsafe(16)
    participant_id = database.create_participant(token, payload.name)
    await _broadcast_state()
    return RegisterResponse(token=token, id=participant_id, name=payload.name.strip())


@app.get("/api/me/{token}")
async def get_me(token: str):
    participant = database.get_participant_by_token(token)
    if participant is None:
        return {"exists": False}
    teams = database.get_results()
    return {
        "exists": True,
        "name": participant["name"],
        "completed": bool(participant["completed_at"]),
        "teams_ready": teams is not None,
        "teams": teams,
        "teams_version": database.get_results_version(),
    }


@app.post("/api/submit")
async def submit(payload: SubmitRequest):
    participant = database.get_participant_by_token(payload.token)
    if participant is None:
        raise HTTPException(status_code=404, detail="Tuntematon osallistuja - aloita alusta.")

    valid_ids = set(question_ids())
    submitted_ids = set(payload.answers.keys())
    if submitted_ids != valid_ids:
        raise HTTPException(status_code=400, detail="Vastaukset eivat kata kaikkia kysymyksia.")
    if any(not (0 <= idx <= 3) for idx in payload.answers.values()):
        raise HTTPException(status_code=400, detail="Virheellinen vastausvaihtoehto.")

    database.save_answers(participant["id"], payload.answers)
    await _broadcast_state()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Admin-API
# ---------------------------------------------------------------------------


@app.post("/api/admin/{secret}/form-teams")
async def admin_form_teams(secret: str, payload: FormTeamsRequest | None = None):
    _check_admin(secret)

    participants = database.get_all_participants()
    completed = [p for p in participants if p["completed_at"]]
    if len(completed) < 2:
        raise HTTPException(
            status_code=400, detail="Liian vahan vastanneita joukkueiden muodostamiseen."
        )

    team_count = (payload.team_count if payload else None) or TEAM_COUNT

    all_answers = database.get_all_answers()
    participant_ids = [p["id"] for p in completed]
    names_by_id = {p["id"]: p["name"] for p in completed}
    qids = question_ids()

    clusters, dist = form_teams(participant_ids, all_answers, qids, k=team_count)
    teams = generate_teams(clusters, all_answers, load_questions(), names_by_id, dist)

    database.save_results(teams)
    await _broadcast_state()
    return {"teams": teams}


@app.post("/api/admin/{secret}/reset")
async def admin_reset(secret: str):
    _check_admin(secret)
    database.reset_all()
    await _broadcast_state()
    return {"ok": True}


@app.get("/api/admin/{secret}/qr")
async def admin_qr(secret: str, request: Request):
    _check_admin(secret)
    base_url = str(request.base_url).rstrip("/")
    img = qrcode.make(base_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@app.get("/api/admin/{secret}/questions")
async def admin_get_questions(secret: str):
    _check_admin(secret)
    return {"questions": load_questions()}


@app.put("/api/admin/{secret}/questions")
async def admin_update_questions(secret: str, payload: QuestionsUpdateRequest):
    _check_admin(secret)
    try:
        normalized = normalize_questions(payload.questions)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    database.save_question_bank(normalized)
    return {"questions": normalized}


@app.post("/api/admin/{secret}/questions/reset-defaults")
async def admin_reset_questions(secret: str):
    _check_admin(secret)
    return {"questions": reset_to_defaults()}


# ---------------------------------------------------------------------------
# WebSocket - reaaliaikaiset paivitykset
# ---------------------------------------------------------------------------


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_text(json.dumps(_current_state()))
        while True:
            # Asiakas ei laheta mitaan - tama vain pitaa yhteyden auki ja
            # havaitsee katkeamisen (WebSocketDisconnect).
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket)
