from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.api.deps import CurrentUser, require_roles
from app.db.session import SessionDep
from app.models import User
from app.models.enums import UserRole
from app.schemas.common import Page
from app.schemas.team import PlayerCreateForm, PlayerProfile, PlayerRead, PlayerUpdate
from app.services import players as players_service

router = APIRouter(prefix="/players", tags=["players"])

Photo = Annotated[UploadFile, File(description="JPEG, PNG или WebP, до 5 МБ")]


@router.get("")
async def search_players(
    session: SessionDep,
    _: Annotated[User, Depends(require_roles(UserRole.team_rep, UserRole.organizer))],
    search: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[PlayerRead]:
    """Поиск по базе игроков, чтобы добавить существующего в команду. С датой рождения."""
    players, total = await players_service.search_players(session, search, limit, offset)
    return Page(items=[PlayerRead.model_validate(p) for p in players], total=total)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_player(
    data: Annotated[PlayerCreateForm, Form()],
    session: SessionDep,
    user: Annotated[User, Depends(require_roles(UserRole.team_rep))],
) -> PlayerRead:
    """Создать игрока (multipart/form-data). ФИО, дата рождения, фото и согласие на ПД обязательны."""
    player = await players_service.create_player(session, user, data)
    return PlayerRead.model_validate(player)


@router.get("/{player_id}")
async def get_player(player_id: int, session: SessionDep) -> PlayerProfile:
    """Публичный профиль: без даты рождения, с командами и статистикой."""
    return await players_service.player_profile(session, player_id)


@router.patch("/{player_id}")
async def update_player(
    player_id: int, data: PlayerUpdate, session: SessionDep, user: CurrentUser
) -> PlayerRead:
    player = await players_service.update_player(session, user, player_id, data)
    return PlayerRead.model_validate(player)


@router.put("/{player_id}/photo")
async def replace_photo(player_id: int, photo: Photo, session: SessionDep, user: CurrentUser) -> PlayerRead:
    player = await players_service.replace_photo(session, user, player_id, photo)
    return PlayerRead.model_validate(player)
