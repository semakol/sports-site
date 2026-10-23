from datetime import datetime

from sqlalchemy import BigInteger, DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Единые имена ограничений, чтобы Alembic генерировал предсказуемые миграции
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    # Все datetime в моделях — timestamptz (храним в UTC)
    type_annotation_map = {datetime: DateTime(timezone=True)}


class IdMixin:
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
