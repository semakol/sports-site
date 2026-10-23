from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/.env — путь не зависит от рабочей папки (запуск из PyCharm, из корня репозитория и т.д.)
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Настройки приложения. Значения берутся из переменных окружения или файла .env."""

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Sports Site API"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://sports:sports@localhost:5432/sports_site"
    test_database_url: str = "postgresql+asyncpg://sports:sports@localhost:5432/sports_site_test"

    # Адреса фронтенда, которым разрешены запросы к API (CORS)
    cors_origins: list[str] = ["http://localhost:5173"]

    # JWT. В .env обязательно задать свой секрет: python -c "import secrets; print(secrets.token_urlsafe(32))"
    jwt_secret_key: str = Field("dev-only-secret-change-me-in-env-file", min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24


settings = Settings()
