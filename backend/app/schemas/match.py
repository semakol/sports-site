import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

from app.models.enums import EventType, MatchStage, MatchStatus, ResultType
from app.schemas.team import PlayerShort, ShirtNumber, TeamShort, UserShort


class TournamentShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class GroupRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class Score(BaseModel):
    home_score: int
    away_score: int


class MatchRead(Score):
    id: int
    tournament: TournamentShort
    stage: MatchStage
    group: GroupRef | None
    round: int
    home_team: TeamShort | None = Field(description="null — соперник ещё не определён")
    away_team: TeamShort | None
    scheduled_at: datetime
    venue: str | None
    status: MatchStatus
    result_type: ResultType | None
    home_penalties: int | None
    away_penalties: int | None
    winner_team_id: int | None
    next_match_id: int | None


class PeriodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    number: int
    started_at: datetime
    ended_at: datetime | None


class LineupPlayerRead(BaseModel):
    player: PlayerShort
    shirt_number: int
    is_starting: bool
    is_captain: bool


class LineupRead(BaseModel):
    team: TeamShort
    submitted_at: datetime
    players: list[LineupPlayerRead]


class Lineups(BaseModel):
    home: LineupRead | None
    away: LineupRead | None


class MatchEventRead(BaseModel):
    id: int
    type: EventType
    player: PlayerShort
    player_in: PlayerShort | None = Field(description="Только для замены: вышедший игрок, player — ушедший")
    team: TeamShort
    period: int
    minute: int


class MatchDetail(MatchRead):
    curator: UserShort | None
    lineup_deadline: datetime
    current_period: int | None
    periods: list[PeriodRead]
    lineups: Lineups
    events: list[MatchEventRead]


class MatchUpdate(BaseModel):
    scheduled_at: AwareDatetime | None = None
    venue: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None = None
    curator_id: int | None = None
    status: Literal[MatchStatus.scheduled, MatchStatus.postponed, MatchStatus.cancelled] | None = None


# ─── заявка ───
class LineupPlayerInput(BaseModel):
    player_id: int
    shirt_number: ShirtNumber
    is_starting: bool
    is_captain: bool = False


class LineupInput(BaseModel):
    players: list[LineupPlayerInput] = Field(min_length=1)


# ─── протокол ───
class MatchEventInput(BaseModel):
    client_event_id: uuid.UUID
    type: EventType
    player_id: int = Field(description="Для замены — уходящий игрок")
    player_in_id: int | None = Field(None, description="Только для замены — выходящий игрок")
    client_ts: AwareDatetime


class MatchEventResult(Score):
    event: MatchEventRead


class FinishRequest(BaseModel):
    """Счёт серии пенальти — только для ничьей в плей-офф."""

    home_penalties: int | None = Field(None, ge=0)
    away_penalties: int | None = Field(None, ge=0)
