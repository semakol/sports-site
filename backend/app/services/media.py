"""Хранение загруженных фото на диске (settings.media_dir), раздаются по адресу /media/..."""

import uuid

from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.errors import AppError

MEDIA_URL = "/media"

# Формат определяем по первым байтам файла, а не по Content-Type от клиента
SIGNATURES = {
    b"\xff\xd8\xff": "jpg",
    b"\x89PNG\r\n\x1a\n": "png",
}


def detect_image_type(head: bytes) -> str | None:
    for signature, ext in SIGNATURES.items():
        if head.startswith(signature):
            return ext
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


def invalid_photo(message: str) -> AppError:
    return AppError(400, "VALIDATION_ERROR", message, field="photo")


async def save_photo(photo: UploadFile, folder: str) -> str:
    """Проверяет и сохраняет фото, возвращает URL вида /media/<folder>/<uuid>.<ext>."""
    max_bytes = settings.max_photo_size_mb * 1024 * 1024
    data = await photo.read(max_bytes + 1)
    if not data:
        raise invalid_photo("Фото обязательно")
    if len(data) > max_bytes:
        raise invalid_photo(f"Фото должно быть не больше {settings.max_photo_size_mb} МБ")
    ext = detect_image_type(data[:12])
    if ext is None:
        raise invalid_photo("Фото должно быть в формате JPEG, PNG или WebP")

    name = f"{folder}/{uuid.uuid4().hex}.{ext}"
    path = settings.media_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    await run_in_threadpool(path.write_bytes, data)
    return f"{MEDIA_URL}/{name}"


def delete_media(url: str | None) -> None:
    """Удаляет файл по URL из save_photo. Чужие и внешние URL игнорирует."""
    if not url or not url.startswith(f"{MEDIA_URL}/"):
        return
    path = (settings.media_dir / url.removeprefix(f"{MEDIA_URL}/")).resolve()
    if path.is_relative_to(settings.media_dir.resolve()):
        path.unlink(missing_ok=True)
