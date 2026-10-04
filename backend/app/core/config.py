from pathlib import Path

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


settings = Settings()
