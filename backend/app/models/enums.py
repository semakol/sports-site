from enum import StrEnum

from sqlalchemy import Enum


def db_enum(enum_cls: type[StrEnum], name: str) -> Enum:
    """Перечисление хранится как VARCHAR + CHECK: новые значения добавляются без ALTER TYPE."""
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=20,
        values_callable=lambda e: [m.value for m in e],
    )


class UserRole(StrEnum):
    admin = "admin"
    organizer = "organizer"
    team_rep = "team_rep"
    curator = "curator"


class TournamentFormat(StrEnum):
    round_robin = "round_robin"
    playoff = "playoff"
    mixed = "mixed"


class TournamentStatus(StrEnum):
    draft = "draft"
    published = "published"
    finished = "finished"


class MatchStage(StrEnum):
    group = "group"
    playoff = "playoff"


class MatchSlot(StrEnum):
    home = "home"
    away = "away"


class MatchStatus(StrEnum):
    scheduled = "scheduled"
    live = "live"
    finished = "finished"
    postponed = "postponed"
    cancelled = "cancelled"


class ResultType(StrEnum):
    regular = "regular"
    penalties = "penalties"
    forfeit = "forfeit"


class EventType(StrEnum):
    goal = "goal"
    own_goal = "own_goal"
    yellow_card = "yellow_card"
    red_card = "red_card"
    substitution = "substitution"
