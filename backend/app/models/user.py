from sqlalchemy import String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, IdMixin
from app.models.enums import UserRole, db_enum


class User(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[UserRole] = mapped_column(db_enum(UserRole, "user_role"), default=UserRole.team_rep)
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
