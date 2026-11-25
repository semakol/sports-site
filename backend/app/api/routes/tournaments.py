from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import OptionalUser, require_roles
from app.api.visibility import visible_tournament
from app.core.errors import Forbidden, Unauthorized
from app.db.session import SessionDep
from app.models import User
from app.models.enums import TournamentStatus, UserRole
from app.schemas.common import Page
from app.schemas.match import MatchRead
from app.schemas.tournament import (
    BracketRound,
    GroupCreate,
    GroupRead,
    GroupStandings,
    PlayerStatRow,
    ScheduleRequest,
    TournamentCreate,
    TournamentRead,
    TournamentTeamRead,
    TournamentTeamsAdd,
    TournamentTeamUpdate,
    TournamentUpdate,
)
from app.services import matches as matches_service
from app.services import public as public_service
from app.services import schedule as schedule_service
from app.services import tournaments as tournaments_service

router = APIRouter(prefix="/tournaments", tags=["tournaments"])

Organizer = Annotated[User, Depends(require_roles(UserRole.organizer))]


@router.get("")
async def list_tournaments(
    session: SessionDep,
    user: OptionalUser,
    status: TournamentStatus | None = None,
    mine: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[TournamentRead]:
    """Опубликованные и завершённые турниры. mine=true — все турниры организатора, включая черновики."""
    if mine and user is None:
        raise Unauthorized()
    if mine and user.role != UserRole.organizer:
        raise Forbidden()
    items, total = await tournaments_service.list_tournaments(
        session, user.id if mine else None, status, limit, offset
    )
    return Page(items=items, total=total)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_tournament(data: TournamentCreate, session: SessionDep, user: Organizer) -> TournamentRead:
    """Создать черновик турнира."""
    return await tournaments_service.create_tournament(session, user, data)


@router.get("/{tournament_id}", dependencies=[Depends(visible_tournament)])
async def get_tournament(tournament_id: int, session: SessionDep) -> TournamentRead:
    return await tournaments_service.read_tournament(session, tournament_id)


@router.patch("/{tournament_id}")
async def update_tournament(
    tournament_id: int, data: TournamentUpdate, session: SessionDep, user: Organizer
) -> TournamentRead:
    """Изменить черновик. Формат меняется только до генерации расписания."""
    return await tournaments_service.update_tournament(session, user, tournament_id, data)


@router.delete("/{tournament_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tournament(tournament_id: int, session: SessionDep, user: Organizer) -> None:
    await tournaments_service.delete_tournament(session, user, tournament_id)


@router.post("/{tournament_id}/publish")
async def publish_tournament(tournament_id: int, session: SessionDep, user: Organizer) -> TournamentRead:
    """Черновик → опубликован. Нужно сгенерированное расписание."""
    return await tournaments_service.publish(session, user, tournament_id)


# ─── группы ───
@router.get("/{tournament_id}/groups", dependencies=[Depends(visible_tournament)])
async def list_groups(tournament_id: int, session: SessionDep) -> list[GroupRead]:
    return await tournaments_service.list_groups(session, tournament_id)


@router.post("/{tournament_id}/groups", status_code=status.HTTP_201_CREATED)
async def create_group(
    tournament_id: int, data: GroupCreate, session: SessionDep, user: Organizer
) -> GroupRead:
    return await tournaments_service.create_group(session, user, tournament_id, data.name)


@router.delete("/{tournament_id}/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(tournament_id: int, group_id: int, session: SessionDep, user: Organizer) -> None:
    """Удалить группу. Её команды остаются в турнире без группы."""
    await tournaments_service.delete_group(session, user, tournament_id, group_id)


# ─── участники ───
@router.get("/{tournament_id}/teams", dependencies=[Depends(visible_tournament)])
async def list_tournament_teams(tournament_id: int, session: SessionDep) -> list[TournamentTeamRead]:
    return await tournaments_service.list_teams(session, tournament_id)


@router.post("/{tournament_id}/teams", status_code=status.HTTP_201_CREATED)
async def add_tournament_teams(
    tournament_id: int, data: TournamentTeamsAdd, session: SessionDep, user: Organizer
) -> list[TournamentTeamRead]:
    return await tournaments_service.add_teams(session, user, tournament_id, data)


@router.patch("/{tournament_id}/teams/{team_id}")
async def update_tournament_team(
    tournament_id: int, team_id: int, data: TournamentTeamUpdate, session: SessionDep, user: Organizer
) -> TournamentTeamRead:
    """Перенести команду в другую группу или задать посев."""
    return await tournaments_service.update_team(session, user, tournament_id, team_id, data)


@router.delete("/{tournament_id}/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tournament_team(
    tournament_id: int, team_id: int, session: SessionDep, user: Organizer
) -> None:
    await tournaments_service.remove_team(session, user, tournament_id, team_id)


# ─── расписание и сетка ───
@router.post("/{tournament_id}/schedule", status_code=status.HTTP_201_CREATED)
async def generate_schedule(
    tournament_id: int, data: ScheduleRequest, session: SessionDep, user: Organizer
) -> list[MatchRead]:
    """round_robin — круг в группах, playoff — сетка по посеву, mixed — группы и пустая сетка плей-офф."""
    return await schedule_service.generate(session, user, tournament_id, data)


@router.delete("/{tournament_id}/schedule", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(tournament_id: int, session: SessionDep, user: Organizer) -> None:
    """Удалить расписание черновика, чтобы поменять группы или участников."""
    await tournaments_service.delete_schedule(session, user, tournament_id)


@router.get("/{tournament_id}/matches", dependencies=[Depends(visible_tournament)])
async def list_tournament_matches(tournament_id: int, session: SessionDep) -> list[MatchRead]:
    await tournaments_service.get_tournament(session, tournament_id)
    return await matches_service.list_tournament_matches(session, tournament_id)


@router.get("/{tournament_id}/bracket", dependencies=[Depends(visible_tournament)])
async def get_bracket(tournament_id: int, session: SessionDep) -> list[BracketRound]:
    """Сетка плей-офф по раундам, от первого до финала."""
    return await schedule_service.bracket(session, tournament_id)


@router.get("/{tournament_id}/standings", dependencies=[Depends(visible_tournament)])
async def standings(tournament_id: int, session: SessionDep) -> list[GroupStandings]:
    """Таблица по завершённым матчам группового этапа; плей-офф не учитывается."""
    return await public_service.standings(session, tournament_id)


@router.get("/{tournament_id}/player-stats", dependencies=[Depends(visible_tournament)])
async def player_stats(
    tournament_id: int,
    session: SessionDep,
    sort: Literal["goals", "yellow_cards", "red_cards"] = "goals",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[PlayerStatRow]:
    return await public_service.player_stats(session, tournament_id, sort, limit)
