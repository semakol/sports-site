from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, Conflict, NotFound
from app.models import (
    Lineup,
    LineupPlayer,
    Match,
    MatchEvent,
    MatchPeriod,
    Player,
    Team,
    Tournament,
    TournamentGroup,
    User,
)
from app.models.enums import MatchStatus, TournamentStatus, UserRole
from app.schemas.match import (
    GroupRef,
    LineupPlayerRead,
    LineupRead,
    Lineups,
    MatchDetail,
    MatchEventRead,
    MatchRead,
    MatchUpdate,
    PeriodRead,
    TournamentShort,
)
from app.schemas.team import PlayerShort, TeamShort, UserShort
from app.services.tournaments import get_own_tournament

LINEUP_DEADLINE = timedelta(hours=1)
NOT_STARTED = (MatchStatus.scheduled, MatchStatus.postponed)


async def get_match(session: AsyncSession, match_id: int) -> Match:
    match = await session.get(Match, match_id)
    if match is None:
        raise NotFound("Матч не найден")
    return match


async def by_id[T](session: AsyncSession, model: type[T], ids: set[int | None]) -> dict[int, T]:
    ids.discard(None)
    if not ids:
        return {}
    return {obj.id: obj for obj in await session.scalars(select(model).where(model.id.in_(ids)))}


async def to_reads(session: AsyncSession, matches: list[Match]) -> list[MatchRead]:
    teams = await by_id(session, Team, {t for m in matches for t in (m.home_team_id, m.away_team_id)})
    groups = await by_id(session, TournamentGroup, {m.group_id for m in matches})
    tournaments = await by_id(session, Tournament, {m.tournament_id for m in matches})

    def team(team_id: int | None) -> TeamShort | None:
        return TeamShort.model_validate(teams[team_id]) if team_id else None

    return [
        MatchRead(
            id=m.id,
            tournament=TournamentShort.model_validate(tournaments[m.tournament_id]),
            stage=m.stage,
            group=GroupRef.model_validate(groups[m.group_id]) if m.group_id else None,
            round=m.round,
            home_team=team(m.home_team_id),
            away_team=team(m.away_team_id),
            scheduled_at=m.scheduled_at,
            venue=m.venue,
            status=m.status,
            home_score=m.home_score,
            away_score=m.away_score,
            result_type=m.result_type,
            home_penalties=m.home_penalties,
            away_penalties=m.away_penalties,
            winner_team_id=m.winner_team_id,
            next_match_id=m.next_match_id,
        )
        for m in matches
    ]


async def list_tournament_matches(session: AsyncSession, tournament_id: int) -> list[MatchRead]:
    matches = await session.scalars(
        select(Match)
        .where(Match.tournament_id == tournament_id)
        .order_by(Match.stage, Match.round, Match.bracket_position, Match.group_id, Match.id)
    )
    return await to_reads(session, list(matches))


async def read_lineup(session: AsyncSession, match_id: int, team_id: int) -> LineupRead | None:
    lineup = await session.scalar(
        select(Lineup).where(Lineup.match_id == match_id, Lineup.team_id == team_id)
    )
    if lineup is None:
        return None
    rows = await session.execute(
        select(LineupPlayer, Player)
        .join(Player, Player.id == LineupPlayer.player_id)
        .where(LineupPlayer.lineup_id == lineup.id)
        .order_by(LineupPlayer.is_starting.desc(), LineupPlayer.shirt_number)
    )
    return LineupRead(
        team=TeamShort.model_validate(await session.get(Team, team_id)),
        submitted_at=lineup.submitted_at,
        players=[
            LineupPlayerRead(
                player=PlayerShort.model_validate(p),
                shirt_number=lp.shirt_number,
                is_starting=lp.is_starting,
                is_captain=lp.is_captain,
            )
            for lp, p in rows
        ],
    )


async def active_events(session: AsyncSession, match_id: int) -> list[MatchEvent]:
    """Неотменённые события в порядке внесения."""
    events = await session.scalars(
        select(MatchEvent)
        .where(MatchEvent.match_id == match_id, MatchEvent.cancelled_at.is_(None))
        .order_by(MatchEvent.id)
    )
    return list(events)


async def events_to_reads(session: AsyncSession, events: list[MatchEvent]) -> list[MatchEventRead]:
    players = await by_id(session, Player, {p for e in events for p in (e.player_id, e.player_in_id)})
    teams = await by_id(session, Team, {e.team_id for e in events})
    return [
        MatchEventRead(
            id=e.id,
            type=e.type,
            player=PlayerShort.model_validate(players[e.player_id]),
            player_in=PlayerShort.model_validate(players[e.player_in_id]) if e.player_in_id else None,
            team=TeamShort.model_validate(teams[e.team_id]),
            period=e.period,
            minute=e.minute,
        )
        for e in sorted(events, key=lambda e: (e.period, e.minute, e.id))
    ]


async def read_detail(session: AsyncSession, match_id: int) -> MatchDetail:
    match = await get_match(session, match_id)
    [base] = await to_reads(session, [match])
    periods = list(
        await session.scalars(
            select(MatchPeriod).where(MatchPeriod.match_id == match.id).order_by(MatchPeriod.number)
        )
    )
    curator = await session.get(User, match.curator_id) if match.curator_id else None
    home = await read_lineup(session, match.id, match.home_team_id) if match.home_team_id else None
    away = await read_lineup(session, match.id, match.away_team_id) if match.away_team_id else None
    return MatchDetail(
        **base.model_dump(),
        curator=UserShort.model_validate(curator) if curator else None,
        lineup_deadline=match.scheduled_at - LINEUP_DEADLINE,
        current_period=next((p.number for p in periods if p.ended_at is None), None),
        periods=[PeriodRead.model_validate(p) for p in periods],
        lineups=Lineups(home=home, away=away),
        events=await events_to_reads(session, await active_events(session, match.id)),
    )


async def update_match(session: AsyncSession, user: User, match_id: int, data: MatchUpdate) -> MatchRead:
    """Организатор переносит или отменяет матч и назначает куратора."""
    match = await get_match(session, match_id)
    await get_own_tournament(session, match.tournament_id, user)
    if match.status not in NOT_STARTED:
        raise Conflict("MATCH_ALREADY_STARTED", "Матч уже начался или завершён")
    changes = data.model_dump(exclude_unset=True)
    if changes.get("curator_id") is not None:
        curator = await session.get(User, changes["curator_id"])
        if curator is None or curator.role != UserRole.curator or not curator.is_active:
            raise AppError(400, "VALIDATION_ERROR", "Пользователь не является куратором", "curator_id")
    for field in ("scheduled_at", "status"):
        if field in changes and changes[field] is None:
            raise AppError(400, "VALIDATION_ERROR", "Поле не может быть пустым", field)
    for field, value in changes.items():
        setattr(match, field, value)
    await session.commit()
    [result] = await to_reads(session, [match])
    return result


async def list_matches(
    session: AsyncSession,
    tournament_id: int | None,
    team_id: int | None,
    statuses: list[MatchStatus],
    date_from: date | None,
    date_to: date | None,
    curator_id: int | None,
    limit: int,
    offset: int,
) -> tuple[list[MatchRead], int]:
    query = (
        select(Match)
        .join(Tournament, Tournament.id == Match.tournament_id)
        .where(Tournament.status != TournamentStatus.draft)
    )
    if tournament_id is not None:
        query = query.where(Match.tournament_id == tournament_id)
    if team_id is not None:
        query = query.where(or_(Match.home_team_id == team_id, Match.away_team_id == team_id))
    if statuses:
        query = query.where(Match.status.in_(statuses))
    if date_from:
        query = query.where(Match.scheduled_at >= datetime.combine(date_from, time.min, UTC))
    if date_to:
        # Верхняя граница включительна, без зависимости от часового пояса PostgreSQL.
        query = query.where(Match.scheduled_at <= datetime.combine(date_to, time.max, UTC))
    if curator_id is not None:
        query = query.where(Match.curator_id == curator_id)
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    matches = list(
        await session.scalars(query.order_by(Match.scheduled_at, Match.id).limit(limit).offset(offset))
    )
    return await to_reads(session, matches), total or 0
