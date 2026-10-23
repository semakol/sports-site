import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    SmallInteger,
    String,
    UniqueConstraint,
    false,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, IdMixin
from app.models.enums import EventType, MatchSlot, MatchStage, MatchStatus, ResultType, db_enum


class Match(IdMixin, Base):
    __tablename__ = "matches"
    __table_args__ = (CheckConstraint("home_team_id <> away_team_id", name="different_teams"),)

    tournament_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tournaments.id", ondelete="CASCADE"), index=True
    )
    stage: Mapped[MatchStage] = mapped_column(db_enum(MatchStage, "match_stage"), default=MatchStage.group)
    group_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tournament_groups.id", ondelete="SET NULL"), index=True
    )
    round: Mapped[int] = mapped_column(SmallInteger)

    # Сетка плей-офф: победитель попадает в слот next_match_slot матча next_match_id
    bracket_position: Mapped[int | None] = mapped_column(SmallInteger)
    next_match_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("matches.id", ondelete="SET NULL")
    )
    next_match_slot: Mapped[MatchSlot | None] = mapped_column(db_enum(MatchSlot, "match_slot"))

    # NULL — соперник в плей-офф ещё не определён
    home_team_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("teams.id"), index=True)
    away_team_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("teams.id"), index=True)
    curator_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    venue: Mapped[str | None] = mapped_column(String(200))
    scheduled_at: Mapped[datetime] = mapped_column(index=True)
    status: Mapped[MatchStatus] = mapped_column(
        db_enum(MatchStatus, "match_status"), default=MatchStatus.scheduled, index=True
    )

    home_score: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    away_score: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    home_penalties: Mapped[int | None] = mapped_column(SmallInteger)
    away_penalties: Mapped[int | None] = mapped_column(SmallInteger)
    result_type: Mapped[ResultType | None] = mapped_column(db_enum(ResultType, "result_type"))
    forfeit_team_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("teams.id"))
    winner_team_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("teams.id"))

    started_at: Mapped[datetime | None]
    finished_at: Mapped[datetime | None]


class MatchPeriod(IdMixin, Base):
    """Тайм матча. Минута события считается по таймам, перерыв в неё не входит."""

    __tablename__ = "match_periods"
    __table_args__ = (UniqueConstraint("match_id", "number"),)

    match_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("matches.id", ondelete="CASCADE"))
    number: Mapped[int] = mapped_column(SmallInteger)
    started_at: Mapped[datetime]
    ended_at: Mapped[datetime | None]


class Lineup(IdMixin, Base):
    """Заявка команды на матч."""

    __tablename__ = "lineups"
    __table_args__ = (UniqueConstraint("match_id", "team_id"),)

    match_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("matches.id", ondelete="CASCADE"))
    team_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("teams.id"), index=True)
    submitted_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    submitted_at: Mapped[datetime]


class LineupPlayer(Base):
    __tablename__ = "lineup_players"

    lineup_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("lineups.id", ondelete="CASCADE"), primary_key=True
    )
    player_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("players.id"), primary_key=True, index=True)
    shirt_number: Mapped[int] = mapped_column(SmallInteger)
    is_starting: Mapped[bool] = mapped_column(default=True, server_default=true())
    is_captain: Mapped[bool] = mapped_column(default=False, server_default=false())


class MatchEvent(IdMixin, CreatedAtMixin, Base):
    """Событие протокола. Отмена — cancelled_at, строка не удаляется."""

    __tablename__ = "match_events"
    __table_args__ = (
        # player_in_id заполнен только у замены
        CheckConstraint(
            "(type = 'substitution') = (player_in_id IS NOT NULL)",
            name="player_in_only_for_substitution",
        ),
    )

    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("matches.id", ondelete="CASCADE"), index=True
    )
    # Для замены — уходящий игрок
    player_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("players.id"), index=True)
    player_in_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("players.id"))
    team_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("teams.id"))
    type: Mapped[EventType] = mapped_column(db_enum(EventType, "event_type"))
    period: Mapped[int] = mapped_column(SmallInteger)
    minute: Mapped[int] = mapped_column(SmallInteger)
    # Защита от дублей при повторной отправке после обрыва связи
    client_event_id: Mapped[uuid.UUID] = mapped_column(unique=True)
    client_ts: Mapped[datetime]
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    cancelled_at: Mapped[datetime | None]
