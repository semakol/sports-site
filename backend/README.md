# Backend — Sports Site API

Серверная часть веб-платформы для любительских футбольных турниров.

**Стек:** Python 3.12, FastAPI, SQLAlchemy 2 (async, asyncpg), Alembic, PostgreSQL, pytest.

## Структура

```
backend/
├── app/
│   ├── main.py          # создание FastAPI-приложения, CORS, подключение роутов
│   ├── cli.py           # служебные команды (создать администратора)
│   ├── core/
│   │   ├── config.py    # настройки из .env
│   │   ├── security.py  # хеширование паролей, JWT
│   │   └── errors.py    # единый формат ошибок {code, message, field}
│   ├── db/
│   │   ├── base.py      # базовый класс моделей (DeclarativeBase)
│   │   └── session.py   # подключение к БД, зависимость get_session
│   ├── models/          # ORM-модели (таблицы) — по ER-диаграмме
│   ├── schemas/         # Pydantic-схемы запросов и ответов
│   ├── services/        # бизнес-логика и работа с БД
│   └── api/
│       ├── deps.py      # текущий пользователь, проверка ролей
│       ├── router.py    # общий роутер с префиксом /api
│       └── routes/      # эндпоинты по разделам (контроллеры)
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
psql -d postgres -c "CREATE DATABASE sports_site OWNER sports LC_COLLATE 'ru_RU.UTF-8' LC_CTYPE 'ru_RU.UTF-8' TEMPLATE template0;"
psql -d postgres -c "CREATE DATABASE sports_site_test OWNER sports LC_COLLATE 'ru_RU.UTF-8' LC_CTYPE 'ru_RU.UTF-8' TEMPLATE template0;"
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

## Пользователи и роли

Регистрация через API (`POST /api/auth/register`) всегда создаёт роль `team_rep`.
Остальные роли выдаёт администратор: `PATCH /api/users/{id}/role`.

Первого администратора создайте командой (пароль спросит в консоли):

```bash
python -m app.cli create-user --email admin@example.com --full-name "Администратор" --role admin
```

Проверить в Swagger (http://localhost:8000/docs): выполнить `POST /api/auth/login`, скопировать
`access_token`, нажать **Authorize** и вставить токен.

## Тесты и линтер

```bash
pytest
ruff check .
ruff format .
```


## Турниры и публичное API

Организатор создаёт черновик (`POST /api/tournaments`), добавляет участников и группы,
генерирует расписание (`POST /api/tournaments/{id}/schedule`) и публикует турнир
(`POST /api/tournaments/{id}/publish`). До публикации карточка и содержимое доступны
только владельцу с JWT; остальные получают 404. `GET /api/tournaments?mine=true`
возвращает турниры текущего организатора, включая черновики.

Без входа доступны опубликованные и завершённые турниры:

- `GET /api/tournaments` — список с фильтром `status`, `limit`, `offset`.
- `GET /api/tournaments/{id}` — карточка; `/teams`, `/groups`, `/matches`, `/bracket` — содержимое.
- `GET /api/matches` — лента: `tournament_id`, `team_id`, `status=live,finished`,
  `date_from`, `date_to`, `limit`, `offset`. Даты включительно в UTC, порядок по дате и ID.
  `curator=me` требует JWT куратора и оставляет только назначенные ему матчи.
- `GET /api/matches/{id}` — карточка, составы и события без персональных дат рождения.
- `GET /api/tournaments/{id}/standings` — таблицы по группам: только завершённые
  матчи группового этапа, настройки очков турнира; порядок по очкам, разнице мячей,
  забитым, затем ID команды. Для чистого плей-офф — пустой массив.
- `GET /api/tournaments/{id}/player-stats?sort=goals&limit=20` — голы и карточки
  в активных и завершённых матчах. Сортировка: `goals`, `yellow_cards`, `red_cards`.
  `matches` — число заявок игрока на такие матчи; отменённые события не учитываются,
  автогол не добавляет гол игроку. Команда берётся из заявки матча.

Таблицы и статистика вычисляются при чтении из результатов и событий; отдельного
сохранения агрегатов в `standings` пока нет. Swagger работающего API: `/docs`.
