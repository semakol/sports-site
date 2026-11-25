from datetime import date, datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from app.models.enums import TournamentFormat, TournamentStatus
from app.schemas.match import MatchRead
from app.schemas.team import PlayerShort, TeamShort, UserShort, reject_null

TournamentName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
GroupName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
Venue = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class TournamentSettings(BaseModel):
    points_win: int = Field(3, ge=0, le=10)
    points_draw: int = Field(1, ge=0, le=10)
    halves_count: int = Field(2, ge=1, le=4)
    half_duration_min: int = Field(25, ge=1, le=60)
    advance_per_group: int | None = Field(None, ge=1, le=16, description="Сколько выходят из группы (mixed)")


class TournamentCreate(TournamentSettings):
    name: TournamentName
    format: TournamentFormat
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def check_dates(self) -> Self:
        if self.end_date < self.start_date:
            raise ValueError("Дата окончания раньше даты начала")
        return self


class TournamentUpdate(BaseModel):
    name: TournamentName | None = None
    format: TournamentFormat | None = None
    start_date: date | None = None
    end_date: date | None = None
    points_win: int | None = Field(None, ge=0, le=10)
    points_draw: int | None = Field(None, ge=0, le=10)
    halves_count: int | None = Field(None, ge=1, le=4)
    half_duration_min: int | None = Field(None, ge=1, le=60)
    advance_per_group: int | None = Field(None, ge=1, le=16)

    _not_null = field_validator(
        "name",
        "format",
        "start_date",
        "end_date",
        "points_win",
        "points_draw",
        "halves_count",
        "half_duration_min",
    )(reject_null)


class TournamentRead(TournamentSettings):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    format: TournamentFormat
    start_date: date
    end_date: date
    status: TournamentStatus
    organizer: UserShort
    teams_count: int


# ─── группы и участники ───
class GroupShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class GroupCreate(BaseModel):
    name: GroupName


class GroupRead(GroupShort):
    teams: list[TeamShort]


class TournamentTeamRead(BaseModel):
    team: TeamShort
    group: GroupShort | None
    seed: int | None


class TournamentTeamsAdd(BaseModel):
    team_ids: list[int] = Field(min_length=1)
    group_id: int | None = None


class TournamentTeamUpdate(BaseModel):
    group_id: int | None = None
    seed: int | None = Field(None, ge=1)


# ─── расписание и сетка ───
class ScheduleRequest(BaseModel):
    first_round_at: datetime
    days_between_rounds: int = Field(7, ge=1, le=60)
    venue: Venue | None = None


class BracketRound(BaseModel):
    round: int
    name: str = Field(examples=["1/2 финала"])
    matches: list[MatchRead]


class StandingRow(BaseModel):
    position: int = 0
    team: TeamShort
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0


class GroupStandings(BaseModel):
    group: GroupShort | None
    rows: list[StandingRow]


class PlayerStatRow(BaseModel):
    player: PlayerShort
    team: TeamShort
    goals: int
    matches: int
    yellow_cards: int
    red_cards: int
