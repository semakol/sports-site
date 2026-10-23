from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.models import User
from app.models.enums import UserRole
from app.services.users import create_user

BACKEND_DIR = Path(__file__).resolve().parents[1]

# Тесты работают с отдельной базой, чтобы не портить данные разработки
test_engine = create_async_engine(settings.test_database_url, poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def migrate_test_db() -> None:
    """Пересоздаёт схему миграциями: заодно проверяет, что upgrade и downgrade работают."""
    cfg = Config(BACKEND_DIR / "alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.test_database_url.replace("%", "%%"))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")


@pytest.fixture(autouse=True)
async def clean_tables() -> AsyncIterator[None]:
    yield
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    async with test_engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


async def override_get_session() -> AsyncIterator[AsyncSession]:
    async with TestSession() as session:
        yield session


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def make_user():
    """Создаёт пользователя напрямую в БД и возвращает (user, заголовки с токеном)."""
    counter = 0

    async def factory(role: UserRole = UserRole.team_rep, password: str = "password123") -> tuple[User, dict]:
        nonlocal counter
        counter += 1
        async with TestSession() as session:
            user = await create_user(
                session, f"{role}{counter}@example.com", password, f"User {counter}", role
            )
        return user, {"Authorization": f"Bearer {create_access_token(user.id)}"}

    return factory
