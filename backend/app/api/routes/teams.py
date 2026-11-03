from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, OptionalUser, require_roles
from app.core.errors import Unauthorized
from app.db.session import SessionDep
from app.models import User
from app.models.enums import UserRole
from app.schemas.common import Page
from app.schemas.team import RosterAdd, RosterEntry, TeamCreate, TeamRead, TeamUpdate
from app.services import teams as teams_service

router = APIRouter(prefix="/teams", tags=["teams"])

TeamRep = Annotated[User, Depends(require_roles(UserRole.team_rep))]


@router.get("")
async def list_teams(
    session: SessionDep,
    user: OptionalUser,
    mine: bool = False,
    search: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[TeamRead]:
    """Список команд. mine=true — только команды текущего представителя."""
    if mine and user is None:
        raise Unauthorized()
    items, total = await teams_service.list_teams(session, user.id if mine else None, search, limit, offset)
    return Page(items=items, total=total)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_team(data: TeamCreate, session: SessionDep, user: TeamRep) -> TeamRead:
    return await teams_service.create_team(session, user, data)


@router.get("/{team_id}")
async def get_team(team_id: int, session: SessionDep) -> TeamRead:
    return await teams_service.read_team(session, team_id)


@router.patch("/{team_id}")
async def update_team(team_id: int, data: TeamUpdate, session: SessionDep, user: CurrentUser) -> TeamRead:
    return await teams_service.update_team(session, user, team_id, data)


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(team_id: int, session: SessionDep, user: CurrentUser) -> None:
    await teams_service.delete_team(session, user, team_id)


@router.get("/{team_id}/players")
async def list_team_players(team_id: int, session: SessionDep) -> list[RosterEntry]:
    """Текущий состав команды (без ушедших игроков)."""
    return await teams_service.roster(session, team_id)


@router.post("/{team_id}/players", status_code=status.HTTP_201_CREATED)
async def add_team_player(
    team_id: int, data: RosterAdd, session: SessionDep, user: CurrentUser
) -> RosterEntry:
    """Добавить в команду игрока, который уже есть в базе."""
    return await teams_service.add_player(session, user, team_id, data.player_id, data.shirt_number)


@router.delete("/{team_id}/players/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_player(team_id: int, player_id: int, session: SessionDep, user: CurrentUser) -> None:
    """Исключить игрока из команды. Игрок остаётся в базе, история матчей сохраняется."""
    await teams_service.remove_player(session, user, team_id, player_id)
