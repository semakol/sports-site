from datetime import date
from typing import Annotated

from fastapi import UploadFile
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints, field_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Url = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
ShirtNumber = Annotated[int, Field(ge=1, le=99)]


def not_in_future(value: date) -> date:
    if value > date.today():
        raise ValueError("Дата рождения не может быть в будущем")
    if value.year < 1900:
        raise ValueError("Некорректная дата рождения")
    return value


BirthDate = Annotated[date, AfterValidator(not_in_future)]


def reject_null(value):
    """Для PATCH: поле можно не передавать, но нельзя явно обнулить."""
    if value is None:
        raise ValueError("Поле не может быть пустым")
    return value


class UserShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str


# ─── игроки ───
class PlayerShort(BaseModel):
    """Публичные данные игрока — без даты рождения."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    last_name: str
    first_name: str
    middle_name: str | None
    photo_url: str


class PlayerRead(PlayerShort):
    """Полные данные — только для представителей команд и организаторов."""

    birth_date: date


class PlayerCreateForm(BaseModel):
    """Форма создания игрока (multipart/form-data)."""

    last_name: Name
    first_name: Name
    middle_name: Name | None = None
    birth_date: BirthDate
    pd_consent: bool = Field(description="Согласие игрока на обработку персональных данных")
    team_id: int | None = Field(None, description="Сразу добавить игрока в эту команду")
    photo: UploadFile = Field(description="JPEG, PNG или WebP, до 5 МБ")


class PlayerUpdate(BaseModel):
    last_name: Name | None = None
    first_name: Name | None = None
    middle_name: Name | None = None
    birth_date: BirthDate | None = None

    _not_null = field_validator("last_name", "first_name", "birth_date")(reject_null)


class PlayerTotals(BaseModel):
    matches: int
    goals: int
    yellow_cards: int
    red_cards: int


class TeamShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    logo_url: str | None


class PlayerProfile(PlayerShort):
    teams: list[TeamShort]
    totals: PlayerTotals


# ─── команды ───
class TeamRead(TeamShort):
    representative: UserShort
    players_count: int


class TeamCreate(BaseModel):
    name: Name
    logo_url: Url | None = None


class TeamUpdate(BaseModel):
    name: Name | None = None
    logo_url: Url | None = None

    _not_null = field_validator("name")(reject_null)


class RosterEntry(BaseModel):
    player: PlayerShort
    shirt_number: int | None


class RosterAdd(BaseModel):
    player_id: int
    shirt_number: ShirtNumber | None = None
