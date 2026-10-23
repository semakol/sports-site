# Документация API

[`openapi.yaml`](openapi.yaml) — контракт API (OpenAPI 3.1): эндпоинты, форматы запросов и ответов, коды ошибок.
Фронтенд и бэкенд работают по нему параллельно. Любое изменение API сначала вносится сюда и согласуется.

## Как посмотреть

- **Онлайн:** открыть https://editor.swagger.io и вставить содержимое `openapi.yaml` (File → Import file).
- **В PyCharm / WebStorm:** открыть `openapi.yaml` — справа появится превью Swagger
  (в Community-версии нужен плагин «OpenAPI (Swagger) Editor»).
- **Локально в браузере:**
  ```bash
  npx @redocly/cli preview-docs docs/openapi.yaml
  ```

## Mock-сервер для фронтенда

Пока бэкенд в разработке, можно поднять фейковый сервер, который отвечает примерами из спецификации:

```bash
npx @stoplight/prism-cli mock docs/openapi.yaml
```

Сервер запустится на http://localhost:4010, например `GET http://localhost:4010/matches`.
Prism проверяет и запросы: если тело не соответствует схеме, вернёт ошибку.

## Swagger реального бэкенда

Когда эндпоинты будут реализованы, актуальная документация будет доступна у запущенного сервера:
http://localhost:8000/docs (генерируется FastAPI из кода).
