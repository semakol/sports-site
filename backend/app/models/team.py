from datetime import date, datetime

from sqlalchemy import BigInteger, ForeignKey, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, IdMixin


class Team(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "teams"

    representative_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    logo_url: Mapped[str | None] = mapped_column(String(500))


class Player(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "players"

    last_name: Mapped[str] = mapped_column(String(100))
    first_name: Mapped[str] = mapped_column(String(100))
    middle_name: Mapped[str | None] = mapped_column(String(100))
    birth_date: Mapped[date]
    photo_url: Mapped[str] = mapped_column(String(500))
    # Согласие на обработку персональных данных (фото и дата рождения)
    pd_consent_at: Mapped[datetime]
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))


class TeamPlayer(IdMixin, Base):
    """Игрок в команде. left_at != NULL — игрок покинул команду (история сохраняется)."""

    __tablename__ = "team_players"
    __table_args__ = (UniqueConstraint("team_id", "player_id"),)

    team_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("teams.id", ondelete="CASCADE"))
    player_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("players.id"), index=True)
    shirt_number: Mapped[int | None] = mapped_column(SmallInteger)
    joined_at: Mapped[date] = mapped_column(server_default=func.current_date())
    left_at: Mapped[date | None]
