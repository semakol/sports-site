"""Заявка на матч и электронный протокол: таймы, события, замены, завершение матча."""

from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, Conflict, Forbidden, NotFound
from app.models import (
    Lineup,
    LineupPlayer,
    Match,
    MatchEvent,
    MatchPeriod,
    Team,
    TeamPlayer,
    Tournament,
    User,
)
from app.models.enums import EventType, MatchStage, MatchStatus, ResultType, TournamentStatus
from app.schemas.match import (
    FinishRequest,
    LineupInput,
    LineupRead,
    MatchDetail,
    MatchEventInput,
    MatchEventResult,
    Score,
)
from app.services import schedule
from app.services.matches import (
    LINEUP_DEADLINE,
    NOT_STARTED,
    active_events,
    events_to_reads,
    get_match,
    read_detail,
    read_lineup,
)
from app.services.teams import ACTIVE

GOALS = (EventType.goal, EventType.own_goal)


def now() -> datetime:
    return datetime.now(UTC)


def invalid(message: str, field: str) -> AppError:
    return AppError(400, "VALIDATION_ERROR", message, field)


async def ensure_published(session: AsyncSession, match: Match) -> None:
    tournament = await session.get(Tournament, match.tournament_id)
    if tournament.status == TournamentStatus.draft:
        raise Conflict("TOURNAMENT_NOT_PUBLISHED", "Турнир ещё не опубликован")


# ─── заявка ───
async def get_lineup(session: AsyncSession, match_id: int, team_id: int) -> LineupRead:
    await get_match(session, match_id)
    lineup = await read_lineup(session, match_id, team_id)
    if lineup is None:
        raise NotFound("Состав ещё не подан")
    return lineup


async def submit_lineup(
    session: AsyncSession, user: User, match_id: int, team_id: int, data: LineupInput
) -> LineupRead:
    match = await get_match(session, match_id)
    if team_id not in (match.home_team_id, match.away_team_id):
        raise NotFound("Команда не играет в этом матче")
    team = await session.get(Team, team_id)
    if team.representative_id != user.id:
        raise Forbidden("Подать состав может только представитель команды")
    await ensure_published(session, match)
    if match.status not in NOT_STARTED or now() > match.scheduled_at - LINEUP_DEADLINE:
        raise Conflict("LINEUP_LOCKED", "Состав можно изменить не позднее чем за 1 час до матча")

    ids = [p.player_id for p in data.players]
    if len(set(ids)) != len(ids):
        raise invalid("Игрок указан в составе дважды", "players")
    if len({p.shirt_number for p in data.players}) != len(ids):
        raise invalid("Номера игроков в составе повторяются", "players")
    if sum(p.is_captain for p in data.players) > 1:
        raise invalid("Капитан может быть только один", "players")
    if not any(p.is_starting for p in data.players):
        raise invalid("В стартовом составе должен быть хотя бы один игрок", "players")
    roster = set(
        await session.scalars(
            select(TeamPlayer.player_id).where(
                TeamPlayer.team_id == team_id, ACTIVE, TeamPlayer.player_id.in_(ids)
            )
        )
    )
    if missing := [i for i in ids if i not in roster]:
        raise invalid(f"Игрок {missing[0]} не состоит в команде", "players")
    opponent = match.away_team_id if team_id == match.home_team_id else match.home_team_id
    in_opponent = await session.scalar(
        select(LineupPlayer.player_id)
        .join(Lineup, Lineup.id == LineupPlayer.lineup_id)
        .where(Lineup.match_id == match.id, Lineup.team_id == opponent, LineupPlayer.player_id.in_(ids))
    )
    if in_opponent:
        raise invalid(f"Игрок {in_opponent} уже заявлен за соперника", "players")

    lineup = await session.scalar(
        select(Lineup).where(Lineup.match_id == match.id, Lineup.team_id == team_id)
    )
    if lineup is None:
        lineup = Lineup(match_id=match.id, team_id=team_id, submitted_by=user.id, submitted_at=now())
        session.add(lineup)
        await session.flush()
    else:
        lineup.submitted_by, lineup.submitted_at = user.id, now()
        await session.execute(delete(LineupPlayer).where(LineupPlayer.lineup_id == lineup.id))
    session.add_all(LineupPlayer(lineup_id=lineup.id, **p.model_dump()) for p in data.players)
    await session.commit()
    return await read_lineup(session, match.id, team_id)


# ─── таймы ───
async def get_curated_match(session: AsyncSession, match_id: int, user: User) -> Match:
    match = await get_match(session, match_id)
    if match.curator_id != user.id:
        raise Forbidden("Протокол ведёт куратор, назначенный на матч")
    return match


async def open_period(session: AsyncSession, match: Match) -> MatchPeriod | None:
    return await session.scalar(
        select(MatchPeriod).where(MatchPeriod.match_id == match.id, MatchPeriod.ended_at.is_(None))
    )


def ensure_live(match: Match) -> None:
    if match.status != MatchStatus.live:
        raise Conflict("MATCH_NOT_LIVE", "Матч не идёт")


async def start(session: AsyncSession, user: User, match_id: int) -> MatchDetail:
    match = await get_curated_match(session, match_id, user)
    await ensure_published(session, match)
    if match.status != MatchStatus.scheduled:
        raise Conflict("MATCH_NOT_SCHEDULED", "Начать можно только запланированный матч")
    if match.home_team_id is None or match.away_team_id is None:
        raise Conflict("TEAMS_NOT_DEFINED", "Соперники в матче ещё не определены")
    match.status, match.started_at = MatchStatus.live, now()
    session.add(MatchPeriod(match_id=match.id, number=1, started_at=match.started_at))
    await session.commit()
    return await read_detail(session, match.id)


async def end_period(session: AsyncSession, user: User, match_id: int) -> MatchDetail:
    match = await get_curated_match(session, match_id, user)
    ensure_live(match)
    period = await open_period(session, match)
    if period is None:
        raise Conflict("NO_ACTIVE_PERIOD", "Сейчас перерыв — тайм не идёт")
    period.ended_at = now()
    await session.commit()
    return await read_detail(session, match.id)


async def start_period(session: AsyncSession, user: User, match_id: int) -> MatchDetail:
    match = await get_curated_match(session, match_id, user)
    ensure_live(match)
    if await open_period(session, match):
        raise Conflict("PERIOD_IN_PROGRESS", "Текущий тайм ещё не закончен")
    tournament = await session.get(Tournament, match.tournament_id)
    played = await session.scalar(
        select(MatchPeriod.number).where(MatchPeriod.match_id == match.id).order_by(MatchPeriod.number.desc())
    )
    if played >= tournament.halves_count:
        raise Conflict("NO_MORE_PERIODS", "Все таймы сыграны — завершите матч")
    session.add(MatchPeriod(match_id=match.id, number=played + 1, started_at=now()))
    await session.commit()
    return await read_detail(session, match.id)


async def finish(session: AsyncSession, user: User, match_id: int, data: FinishRequest) -> MatchDetail:
    match = await get_curated_match(session, match_id, user)
    ensure_live(match)
    penalties = data.home_penalties, data.away_penalties
    playoff_draw = match.stage == MatchStage.playoff and match.home_score == match.away_score

    if playoff_draw:
        if None in penalties or penalties[0] == penalties[1]:
            raise Conflict(
                "PENALTIES_REQUIRED",
                "Ничья в плей-офф: укажите счёт серии пенальти с победителем",
                field="home_penalties",
            )
        match.home_penalties, match.away_penalties = penalties
        match.result_type = ResultType.penalties
        home_wins = penalties[0] > penalties[1]
    else:
        if penalties != (None, None):
            raise invalid("Серия пенальти бывает только при ничьей в плей-офф", "home_penalties")
        match.result_type = ResultType.regular
        home_wins = match.home_score > match.away_score if match.home_score != match.away_score else None

    if home_wins is not None:
        match.winner_team_id = match.home_team_id if home_wins else match.away_team_id
    if period := await open_period(session, match):
        period.ended_at = now()
    match.status, match.finished_at = MatchStatus.finished, now()
    await schedule.on_match_finished(session, match)
    await session.commit()
    return await read_detail(session, match.id)


# ─── события ───
def replay(starting: set[int], events: list[MatchEvent]) -> set[int]:
    """Проигрывает события по порядку и возвращает игроков на поле.

    Проверяет, что каждое событие возможно: гол забивает игрок на поле, удалённый не возвращается,
    уходит с поля тот, кто на нём, а выходит тот, кого на поле нет. Возвратные замены разрешены.
    """
    on_field, sent_off = set(starting), set()
    for e in events:
        if e.player_id in sent_off:
            raise Conflict("PLAYER_SENT_OFF", "Игрок удалён с поля", field="player_id")
        if e.type in GOALS and e.player_id not in on_field:
            raise Conflict("PLAYER_NOT_ON_FIELD", "Игрока сейчас нет на поле", field="player_id")
        if e.type == EventType.red_card:
            on_field.discard(e.player_id)
            sent_off.add(e.player_id)
        if e.type == EventType.substitution:
            if e.player_id not in on_field:
                raise Conflict("PLAYER_NOT_ON_FIELD", "Уходящего игрока нет на поле", field="player_id")
            if e.player_in_id in sent_off:
                raise Conflict(
                    "PLAYER_SENT_OFF", "Удалённый игрок не может выйти на замену", field="player_in_id"
                )
            if e.player_in_id in on_field:
                raise Conflict("PLAYER_ALREADY_ON_FIELD", "Выходящий игрок уже на поле", field="player_in_id")
            on_field.remove(e.player_id)
            on_field.add(e.player_in_id)
    return on_field


async def lineup_players(session: AsyncSession, match: Match) -> dict[int, tuple[int, bool]]:
    """Заявленные игроки матча: player_id → (team_id, в стартовом составе)."""
    rows = await session.execute(
        select(LineupPlayer.player_id, Lineup.team_id, LineupPlayer.is_starting)
        .join(Lineup, Lineup.id == LineupPlayer.lineup_id)
        .where(Lineup.match_id == match.id)
    )
    return {player_id: (team_id, starting) for player_id, team_id, starting in rows}


def starting_players(players: dict[int, tuple[int, bool]]) -> set[int]:
    return {p for p, (_, starting) in players.items() if starting}


def recount_score(match: Match, events: list[MatchEvent]) -> None:
    home = sum(
        1
        for e in events
        if (e.type == EventType.goal and e.team_id == match.home_team_id)
        or (e.type == EventType.own_goal and e.team_id == match.away_team_id)
    )
    away = sum(1 for e in events if e.type in GOALS) - home
    match.home_score, match.away_score = home, away


async def list_events(session: AsyncSession, match_id: int):
    await get_match(session, match_id)
    return await events_to_reads(session, await active_events(session, match_id))


async def event_result(session: AsyncSession, match: Match, event: MatchEvent) -> MatchEventResult:
    [read] = await events_to_reads(session, [event])
    return MatchEventResult(event=read, home_score=match.home_score, away_score=match.away_score)


async def add_event(
    session: AsyncSession, user: User, match_id: int, data: MatchEventInput
) -> tuple[MatchEventResult, bool]:
    """Вносит событие. Возвращает (результат, создано ли новое)."""
    match = await get_curated_match(session, match_id, user)
    existing = await session.scalar(
        select(MatchEvent).where(MatchEvent.client_event_id == data.client_event_id)
    )
    if existing is not None:  # повторная отправка после обрыва связи — без дубля
        if existing.match_id != match.id:
            raise Conflict("DUPLICATE_EVENT_ID", "client_event_id уже использован", field="client_event_id")
        return await event_result(session, match, existing), False

    ensure_live(match)
    period = await open_period(session, match)
    if period is None:
        raise Conflict("NO_ACTIVE_PERIOD", "Сейчас перерыв — тайм не идёт")

    players = await lineup_players(session, match)
    if data.player_id not in players:
        raise invalid("Игрок не заявлен на матч", "player_id")
    team_id = players[data.player_id][0]
    if data.type == EventType.substitution:
        if data.player_in_id is None:
            raise invalid("Укажите выходящего на замену игрока", "player_in_id")
        if players.get(data.player_in_id, (None,))[0] != team_id:
            raise invalid("Выходящий игрок не заявлен за эту команду", "player_in_id")
    elif data.player_in_id is not None:
        raise invalid("player_in_id указывается только для замены", "player_in_id")

    tournament = await session.get(Tournament, match.tournament_id)
    moment = min(max(data.client_ts, period.started_at), now())
    minute = (
        tournament.half_duration_min * (period.number - 1)
        + int((moment - period.started_at).total_seconds() // 60)
        + 1
    )
    event = MatchEvent(
        match_id=match.id,
        player_id=data.player_id,
        player_in_id=data.player_in_id,
        team_id=team_id,
        type=data.type,
        period=period.number,
        minute=minute,
        client_event_id=data.client_event_id,
        client_ts=data.client_ts,
        created_by=user.id,
    )
    events = [*await active_events(session, match.id), event]
    replay(starting_players(players), events)

    session.add(event)
    recount_score(match, events)
    await session.commit()
    return await event_result(session, match, event), True


async def cancel_event(session: AsyncSession, user: User, match_id: int, event_id: int) -> Score:
    match = await get_curated_match(session, match_id, user)
    event = await session.get(MatchEvent, event_id)
    if event is None or event.match_id != match.id or event.cancelled_at is not None:
        raise NotFound("Событие не найдено")
    if match.status != MatchStatus.live:
        raise Conflict("PROTOCOL_CLOSED", "Протокол закрыт — события менять нельзя")

    events = [e for e in await active_events(session, match.id) if e.id != event.id]
    try:
        replay(starting_players(await lineup_players(session, match)), events)
    except Conflict:
        raise Conflict(
            "EVENT_HAS_DEPENDENTS", "Сначала отмените более поздние события с участием этих игроков"
        ) from None
    event.cancelled_at = now()
    recount_score(match, events)
    await session.commit()
    return Score(home_score=match.home_score, away_score=match.away_score)
