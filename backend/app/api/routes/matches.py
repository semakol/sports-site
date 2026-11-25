from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Body, Depends, Query, Response, status

from app.api.deps import CurrentUser, OptionalUser, require_roles
from app.api.visibility import visible_match
from app.core.errors import AppError, Forbidden, Unauthorized
from app.db.session import SessionDep
from app.models import User
from app.models.enums import UserRole
from app.schemas.common import Page
from app.schemas.match import (
    FinishRequest,
    LineupInput,
    LineupRead,
    MatchDetail,
    MatchEventInput,
    MatchEventRead,
    MatchEventResult,
    MatchRead,
    MatchUpdate,
    Score,
)
from app.services import matches as matches_service
from app.services import protocol

router = APIRouter(prefix="/matches", tags=["matches"])

Organizer = Annotated[User, Depends(require_roles(UserRole.organizer))]
Curator = Annotated[User, Depends(require_roles(UserRole.curator))]


@router.get("")
async def list_matches(
    session: SessionDep,
    user: OptionalUser,
    tournament_id: int | None = None,
    team_id: int | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    curator: Literal["me"] | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[MatchRead]:
    """Лента опубликованных турниров. Даты включительно, в UTC."""
    from app.models.enums import MatchStatus

    if date_from and date_to and date_from > date_to:
        raise AppError(400, "VALIDATION_ERROR", "Дата окончания раньше даты начала", "date_to")
    try:
        statuses = [MatchStatus(value.strip()) for value in status.split(",")] if status is not None else []
    except ValueError:
        raise AppError(400, "VALIDATION_ERROR", "Неизвестный статус матча", "status") from None
    if curator:
        if user is None:
            raise Unauthorized()
        if user.role != UserRole.curator:
            raise Forbidden()
    items, total = await matches_service.list_matches(
        session,
        tournament_id,
        team_id,
        statuses,
        date_from,
        date_to,
        user.id if curator else None,
        limit,
        offset,
    )
    return Page(items=items, total=total)


@router.get("/{match_id}", dependencies=[Depends(visible_match)])
async def get_match(match_id: int, session: SessionDep) -> MatchDetail:
    """Карточка матча с составами и протоколом."""
    return await matches_service.read_detail(session, match_id)


@router.patch("/{match_id}")
async def update_match(match_id: int, data: MatchUpdate, session: SessionDep, user: Organizer) -> MatchRead:
    """Перенести или отменить матч, назначить куратора."""
    return await matches_service.update_match(session, user, match_id, data)


# ─── заявка ───
@router.get("/{match_id}/lineups/{team_id}", dependencies=[Depends(visible_match)], tags=["lineups"])
async def get_lineup(match_id: int, team_id: int, session: SessionDep) -> LineupRead:
    return await protocol.get_lineup(session, match_id, team_id)


@router.put("/{match_id}/lineups/{team_id}", tags=["lineups"])
async def submit_lineup(
    match_id: int, team_id: int, data: LineupInput, session: SessionDep, user: CurrentUser
) -> LineupRead:
    """Подать или изменить состав. Не позже чем за 1 час до матча, иначе 409 LINEUP_LOCKED."""
    return await protocol.submit_lineup(session, user, match_id, team_id, data)


# ─── протокол ───
@router.post("/{match_id}/start", tags=["protocol"])
async def start_match(match_id: int, session: SessionDep, user: Curator) -> MatchDetail:
    return await protocol.start(session, user, match_id)


@router.post("/{match_id}/end-period", tags=["protocol"])
async def end_period(match_id: int, session: SessionDep, user: Curator) -> MatchDetail:
    return await protocol.end_period(session, user, match_id)


@router.post("/{match_id}/start-period", tags=["protocol"])
async def start_period(match_id: int, session: SessionDep, user: Curator) -> MatchDetail:
    return await protocol.start_period(session, user, match_id)


@router.post("/{match_id}/finish", tags=["protocol"])
async def finish_match(
    match_id: int,
    session: SessionDep,
    user: Curator,
    data: Annotated[FinishRequest | None, Body()] = None,
) -> MatchDetail:
    """Завершить матч и закрыть протокол. Для ничьей в плей-офф нужен счёт серии пенальти."""
    return await protocol.finish(session, user, match_id, data or FinishRequest())


@router.get("/{match_id}/events", dependencies=[Depends(visible_match)], tags=["protocol"])
async def list_events(match_id: int, session: SessionDep) -> list[MatchEventRead]:
    return await protocol.list_events(session, match_id)


@router.post("/{match_id}/events", status_code=status.HTTP_201_CREATED, tags=["protocol"])
async def add_event(
    match_id: int, data: MatchEventInput, response: Response, session: SessionDep, user: Curator
) -> MatchEventResult:
    """Внести событие. Минуту и команду определяет сервер. Повтор с тем же client_event_id — 200 без дубля."""
    result, created = await protocol.add_event(session, user, match_id, data)
    if not created:
        response.status_code = status.HTTP_200_OK
    return result


@router.delete("/{match_id}/events/{event_id}", tags=["protocol"])
async def cancel_event(match_id: int, event_id: int, session: SessionDep, user: Curator) -> Score:
    """Отменить событие до закрытия протокола. Возвращает актуальный счёт."""
    return await protocol.cancel_event(session, user, match_id, event_id)
