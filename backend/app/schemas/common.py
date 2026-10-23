from pydantic import BaseModel


class Page[T](BaseModel):
    """Страница списка: { items, total }."""

    items: list[T]
    total: int
