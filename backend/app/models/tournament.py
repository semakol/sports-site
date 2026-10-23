from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, IdMixin
from app.models.enums import TournamentFormat, TournamentStatus, db_enum


class Tournament(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "tournaments"
    __table_args__ = (CheckConstraint("end_date >= start_date", name="dates_order"),)

    organizer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    format: Mapped[TournamentFormat] = mapped_column(db_enum(TournamentFormat, "tournament_format"))
    status: Mapped[TournamentStatus] = mapped_column(
        db_enum(TournamentStatus, "tournament_status"), default=TournamentStatus.draft
    )
    start_date: Mapped[date]
    end_date: Mapped[date]
    points_win: Mapped[int] = mapped_column(SmallInteger, default=3, server_default="3")
    points_draw: Mapped[int] = mapped_column(SmallInteger, default=1, server_default="1")
    halves_count: Mapped[int] = mapped_column(SmallInteger, default=2, server_default="2")
    half_duration_min: Mapped[int] = mapped_column(SmallInteger, default=25, server_default="25")
    # Сколько команд выходит из группы в плей-офф (формат mixed)
    advance_per_group: Mapped[int | None] = mapped_column(SmallInteger)


class TournamentGroup(IdMixin, Base):
    __tablename__ = "tournament_groups"
    __table_args__ = (UniqueConstraint("tournament_id", "name"),)

    tournament_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tournaments.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(50))


class TournamentTeam(IdMixin, Base):
    __tablename__ = "tournament_teams"
    __table_args__ = (UniqueConstraint("tournament_id", "team_id"),)

    tournament_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tournaments.id", ondelete="CASCADE"))
    team_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("teams.id"), index=True)
    group_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tournament_groups.id", ondelete="SET NULL"), index=True
    )
    seed: Mapped[int | None] = mapped_column(SmallInteger)


class Standing(IdMixin, Base):
    """Строка турнирной таблицы. Пересчитывается при закрытии протокола матча."""

    __tablename__ = "standings"
    __table_args__ = (UniqueConstraint("tournament_id", "team_id"),)

    tournament_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tournaments.id", ondelete="CASCADE"))
    group_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tournament_groups.id", ondelete="SET NULL"), index=True
    )
    team_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("teams.id"), index=True)
    position: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    played: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    won: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    drawn: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    lost: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    goals_for: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    goals_against: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    points: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
