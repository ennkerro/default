"""Pydantic-mallit API:n pyynnoille ja vastauksille."""
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=40)


class RegisterResponse(BaseModel):
    token: str
    id: int
    name: str


class SubmitRequest(BaseModel):
    token: str
    answers: dict[str, int]


class FormTeamsRequest(BaseModel):
    team_count: int | None = Field(default=None, ge=2, le=10)


class ParticipantState(BaseModel):
    exists: bool
    name: str | None = None
    completed: bool = False
    teams_ready: bool = False


class StateResponse(BaseModel):
    total: int
    completed: int
    teams_ready: bool
    names: list[str]


class AdminParticipant(BaseModel):
    id: int
    name: str
    completed: bool


class TeamResult(BaseModel):
    index: int
    emoji: str
    name: str
    members: list[str]
    reasons: list[str]
    diagnosis: str
    compatibility_percent: float


class FormTeamsResponse(BaseModel):
    teams: list[TeamResult]
