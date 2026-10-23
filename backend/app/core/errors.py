"""Единый формат ошибок API: {"code": ..., "message": ..., "field": ...} (см. docs/openapi.yaml)."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str, field: str | None = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.field = field


class Unauthorized(AppError):
    def __init__(self, message: str = "Требуется авторизация", code: str = "UNAUTHORIZED"):
        super().__init__(401, code, message)


class Forbidden(AppError):
    def __init__(self, message: str = "Недостаточно прав для этого действия", code: str = "FORBIDDEN"):
        super().__init__(403, code, message)


class NotFound(AppError):
    def __init__(self, message: str = "Объект не найден"):
        super().__init__(404, "NOT_FOUND", message)


class Conflict(AppError):
    def __init__(self, code: str, message: str, field: str | None = None):
        super().__init__(409, code, message, field)


HTTP_CODES = {401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}


def error_body(code: str, message: str, field: str | None = None) -> dict:
    return {"code": code, "message": message, "field": field}


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(error_body(exc.code, exc.message, exc.field), exc.status_code, headers=headers)


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Ошибки валидации отдаём как 400 (а не 422 FastAPI по умолчанию), в field — путь к полю."""
    first = exc.errors()[0]
    loc = [str(p) for p in first.get("loc", ()) if p not in ("body", "query", "path")]
    return JSONResponse(
        error_body("VALIDATION_ERROR", first.get("msg", "Невалидные данные"), ".".join(loc) or None), 400
    )


async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = HTTP_CODES.get(exc.status_code, "HTTP_ERROR")
    return JSONResponse(error_body(code, str(exc.detail)), exc.status_code, headers=exc.headers)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
