# Backend — Sports Site API

Серверная часть веб-платформы для любительских футбольных турниров.

**Стек:** Python 3.12, FastAPI, SQLAlchemy 2 (async, asyncpg), Alembic, PostgreSQL, pytest.

## Структура

```
backend/
├── app/
│   ├── main.py          # создание FastAPI-приложения, CORS, подключение роутов
│   ├── core/config.py   # настройки из .env
│   ├── db/
│   │   ├── base.py      # базовый класс моделей (DeclarativeBase)
│   │   └── session.py   # подключение к БД, зависимость get_session
│   ├── models/          # ORM-модели (таблицы)
│   └── api/
│       ├── router.py    # общий роутер с префиксом /api
│       └── routes/      # эндпоинты по разделам
├── alembic/             # миграции БД
├── tests/               # тесты (pytest), работают с отдельной базой
├── docker-compose.yml   # PostgreSQL в Docker (если не хотите ставить локально)
└── .env.example         # шаблон настроек
```

## Быстрый старт

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Дальше нужна база данных — один из двух вариантов ниже.

## Настройка локальной БД

### Вариант 1: PostgreSQL, установленный локально (macOS, Homebrew)

```bash
brew install postgresql@16
brew services start postgresql@16

psql -d postgres -c "CREATE ROLE sports WITH LOGIN PASSWORD 'sports';"
psql -d postgres -c "CREATE DATABASE sports_site OWNER sports;"
psql -d postgres -c "CREATE DATABASE sports_site_test OWNER sports;"
```

### Вариант 2: PostgreSQL в Docker

```bash
docker compose up -d
```

База для тестов `sports_site_test` создаётся автоматически при первом запуске контейнера.

### Миграции

```bash
alembic upgrade head                              # применить все миграции
alembic revision --autogenerate -m "add teams"    # создать миграцию по изменениям моделей
alembic downgrade -1                              # откатить последнюю миграцию
```

Новую модель нужно импортировать в `app/models/__init__.py`, иначе Alembic её не увидит.

## Запуск

```bash
uvicorn app.main:app --reload
```

- API: http://localhost:8000/api
- Проверка работы и связи с БД: http://localhost:8000/api/health
- Swagger: http://localhost:8000/docs

### Запуск и отладка в PyCharm

В репозитории лежат готовые конфигурации запуска (папка `.run/` в корне), PyCharm подхватывает их сам:

- **Backend API** — сервер на http://localhost:8000. Debug (🐞) — точки останова в эндпоинтах срабатывают.
- **Backend tests** — все тесты из `backend/tests`, тоже можно запускать под отладчиком.

Перед первым запуском: Settings → Project → Python Interpreter → `backend/.venv/bin/python`,
а папку `backend` отметить как Sources Root (ПКМ → Mark Directory as → Sources Root).

Конфигурация запускает сервер без `--reload`, чтобы отладчик работал стабильно: после изменения кода
перезапустите её (⌘F5).

## Тесты и линтер

```bash
pytest
ruff check .
ruff format .
```
