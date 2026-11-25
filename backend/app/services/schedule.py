"""Генерация расписания: круговой этап в группах, сетка плей-офф и продвижение победителей по сетке."""

from collections.abc import Callable
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Conflict
from app.models import Match, Tournament, TournamentGroup, TournamentTeam, User
from app.models.enums import MatchSlot, MatchStage, MatchStatus, TournamentFormat, TournamentStatus
from app.schemas.match import MatchRead
from app.schemas.tournament import BracketRound, ScheduleRequest
from app.services.matches import NOT_STARTED, list_tournament_matches, to_reads
from app.services.tournaments import ensure_draft, get_own_tournament, get_tournament, has_schedule

Pairs = list[tuple[int, int]]


def round_robin(team_ids: list[int]) -> list[Pairs]:
    """Круговая система методом «карусели»: каждая пара встречается один раз.

    При нечётном числе команд одна команда в каждом туре отдыхает.
    """
    teams: list[int | None] = list(team_ids)
    if len(teams) % 2:
        teams.append(None)
    n = len(teams)
    rounds = []
    for r in range(n - 1):
        pairs = []
        for i in range(n // 2):
            home, away = teams[i], teams[n - 1 - i]
            if i == 0 and r % 2:  # первая команда не должна всегда играть дома
                home, away = away, home
            if home is not None and away is not None:
                pairs.append((home, away))
        rounds.append(pairs)
        teams = [teams[0], teams[-1], *teams[1:-1]]
    return rounds


def seeding_order(size: int) -> list[int]:
    """Номера посева по слотам первого раунда: для 8 — 1, 8, 4, 5, 2, 7, 3, 6.

    Сильнейшие посеянные встречаются как можно позже, 1-й и 2-й — только в финале.
    """
    order = [1]
    while len(order) < size:
        total = len(order) * 2 + 1
        order = [s for seed in order for s in (seed, total - seed)]
    return order


def is_power_of_two(n: int) -> bool:
    return n >= 2 and n & (n - 1) == 0


def round_name(round_: int, total_rounds: int) -> str:
    left = total_rounds - round_
    return "Финал" if left == 0 else f"1/{2**left} финала"


async def group_pools(
    session: AsyncSession, tournament: Tournament, entries: list[TournamentTeam]
) -> list[tuple[int | None, list[int]]]:
    """Команды по группам для кругового этапа. Без групп весь турнир — одна группа."""
    groups = list(
        await session.scalars(
            select(TournamentGroup)
            .where(TournamentGroup.tournament_id == tournament.id)
            .order_by(TournamentGroup.name, TournamentGroup.id)
        )
    )
    if not groups:
        if tournament.format == TournamentFormat.mixed:
            raise Conflict("GROUPS_REQUIRED", "Для смешанного формата создайте группы")
        return [(None, [e.team_id for e in entries])]

    if any(e.group_id is None for e in entries):
        raise Conflict("TEAMS_WITHOUT_GROUP", "Распределите все команды по группам")
    min_size = max(2, tournament.advance_per_group or 0)
    pools = []
    for group in groups:
        team_ids = [e.team_id for e in entries if e.group_id == group.id]
        if len(team_ids) < min_size:
            raise Conflict("GROUP_TOO_SMALL", f"В группе {group.name} должно быть минимум {min_size} команды")
        pools.append((group.id, team_ids))
    return pools


async def create_bracket(
    session: AsyncSession,
    tournament: Tournament,
    teams: list[int | None],
    at: Callable[[int], datetime],
    venue: str | None,
    with_byes: bool,
) -> None:
    """Создаёт сетку на len(teams) мест (степень двойки), от финала к первому раунду.

    teams — команды в порядке посева. None — пустое место: при with_byes это «пропуск тура»
    (соперник посеянного сразу проходит дальше), иначе слот заполнится после группового этапа.
    """
    size = len(teams)
    total_rounds = size.bit_length() - 1
    later: list[Match] = []
    for round_ in range(total_rounds, 0, -1):
        current = []
        for pos in range(size >> round_):
            match = Match(
                tournament_id=tournament.id,
                stage=MatchStage.playoff,
                round=round_,
                bracket_position=pos + 1,
                scheduled_at=at(round_ - 1),
                venue=venue,
            )
            if later:
                match.next_match_id = later[pos // 2].id
                match.next_match_slot = MatchSlot.home if pos % 2 == 0 else MatchSlot.away
            current.append(match)
        session.add_all(current)
        await session.flush()
        later = current

    order = seeding_order(size)
    for pos, match in enumerate(later):
        home, away = teams[order[2 * pos] - 1], teams[order[2 * pos + 1] - 1]
        if with_byes and (home is None or away is None):
            await move_to_next(session, match, home or away)
            await session.delete(match)
        else:
            match.home_team_id, match.away_team_id = home, away


async def move_to_next(session: AsyncSession, match: Match, team_id: int | None) -> None:
    if match.next_match_id is None or team_id is None:
        return
    next_match = await session.get(Match, match.next_match_id)
    setattr(next_match, f"{match.next_match_slot}_team_id", team_id)


async def generate(
    session: AsyncSession, user: User, tournament_id: int, data: ScheduleRequest
) -> list[MatchRead]:
    tournament = await get_own_tournament(session, tournament_id, user)
    ensure_draft(tournament)
    if await has_schedule(session, tournament.id):
        raise Conflict("SCHEDULE_GENERATED", "Расписание уже создано — удалите его, чтобы создать заново")
    entries = list(
        await session.scalars(
            select(TournamentTeam)
            .where(TournamentTeam.tournament_id == tournament.id)
            .order_by(TournamentTeam.seed.nulls_last(), TournamentTeam.id)
        )
    )
    if len(entries) < 2:
        raise Conflict("NOT_ENOUGH_TEAMS", "Для расписания нужно минимум две команды")

    def at(round_index: int) -> datetime:
        return data.first_round_at + timedelta(days=data.days_between_rounds * round_index)

    if tournament.format == TournamentFormat.playoff:
        size = 1 << (len(entries) - 1).bit_length()
        teams = [e.team_id for e in entries] + [None] * (size - len(entries))
        await create_bracket(session, tournament, teams, at, data.venue, with_byes=True)
    else:
        pools = await group_pools(session, tournament, entries)
        if tournament.format == TournamentFormat.mixed:
            if not tournament.advance_per_group:
                raise Conflict("ADVANCE_PER_GROUP_REQUIRED", "Укажите, сколько команд выходит из группы")
            if not is_power_of_two(len(pools) * tournament.advance_per_group):
                raise Conflict(
                    "INVALID_BRACKET_SIZE",
                    "Число команд в плей-офф (группы × выходящие) должно быть 2, 4, 8 или 16",
                )
        group_rounds = 0
        for group_id, team_ids in pools:
            rounds = round_robin(team_ids)
            group_rounds = max(group_rounds, len(rounds))
            session.add_all(
                Match(
                    tournament_id=tournament.id,
                    stage=MatchStage.group,
                    group_id=group_id,
                    round=r + 1,
                    home_team_id=home,
                    away_team_id=away,
                    scheduled_at=at(r),
                    venue=data.venue,
                )
                for r, pairs in enumerate(rounds)
                for home, away in pairs
            )
        if tournament.format == TournamentFormat.mixed:
            size = len(pools) * tournament.advance_per_group
            await create_bracket(
                session,
                tournament,
                [None] * size,
                lambda r: at(group_rounds + r),
                data.venue,
                with_byes=False,
            )
    await session.commit()
    return await list_tournament_matches(session, tournament.id)


async def bracket(session: AsyncSession, tournament_id: int) -> list[BracketRound]:
    await get_tournament(session, tournament_id)
    matches = list(
        await session.scalars(
            select(Match)
            .where(Match.tournament_id == tournament_id, Match.stage == MatchStage.playoff)
            .order_by(Match.round, Match.bracket_position)
        )
    )
    if not matches:
        return []
    total_rounds = matches[-1].round
    reads = await to_reads(session, matches)
    return [
        BracketRound(
            round=r,
            name=round_name(r, total_rounds),
            matches=[m for m in reads if m.round == r],
        )
        for r in sorted({m.round for m in reads})
    ]


async def group_table(session: AsyncSession, tournament: Tournament, group_id: int) -> list[int]:
    """Команды группы по местам: очки, разница мячей, забитые.

    Личные встречи пока не учитываются — правило ждёт решения аналитика.
    """
    team_ids = list(
        await session.scalars(
            select(TournamentTeam.team_id).where(
                TournamentTeam.tournament_id == tournament.id, TournamentTeam.group_id == group_id
            )
        )
    )
    stats = {t: [0, 0, 0] for t in team_ids}  # очки, разница, забитые
    matches = await session.scalars(
        select(Match).where(
            Match.tournament_id == tournament.id,
            Match.group_id == group_id,
            Match.stage == MatchStage.group,
            Match.status == MatchStatus.finished,
        )
    )
    for m in matches:
        for team, scored, conceded in (
            (m.home_team_id, m.home_score, m.away_score),
            (m.away_team_id, m.away_score, m.home_score),
        ):
            row = stats.setdefault(team, [0, 0, 0])
            row[0] += (
                tournament.points_win
                if scored > conceded
                else tournament.points_draw
                if scored == conceded
                else 0
            )
            row[1] += scored - conceded
            row[2] += scored
    return sorted(stats, key=lambda t: (-stats[t][0], -stats[t][1], -stats[t][2], t))


async def fill_playoff_from_groups(session: AsyncSession, tournament: Tournament) -> None:
    """После группового этапа: победители групп получают лучший посев, A1 играет с B2, B1 — с A2."""
    groups = await session.scalars(
        select(TournamentGroup.id)
        .where(TournamentGroup.tournament_id == tournament.id)
        .order_by(TournamentGroup.name, TournamentGroup.id)
    )
    tables = [await group_table(session, tournament, g) for g in groups]
    seeds = [table[place] for place in range(tournament.advance_per_group) for table in tables]
    first_round = list(
        await session.scalars(
            select(Match)
            .where(Match.tournament_id == tournament.id, Match.stage == MatchStage.playoff, Match.round == 1)
            .order_by(Match.bracket_position)
        )
    )
    order = seeding_order(len(seeds))
    for pos, match in enumerate(first_round):
        match.home_team_id = seeds[order[2 * pos] - 1]
        match.away_team_id = seeds[order[2 * pos + 1] - 1]


async def unfinished_count(session: AsyncSession, tournament_id: int, stage: MatchStage | None = None) -> int:
    query = select(func.count()).where(
        Match.tournament_id == tournament_id, Match.status.in_((*NOT_STARTED, MatchStatus.live))
    )
    if stage is not None:
        query = query.where(Match.stage == stage)
    return await session.scalar(query) or 0


async def on_match_finished(session: AsyncSession, match: Match) -> None:
    """Победитель уходит в следующий матч сетки; после групп заполняется плей-офф; турнир завершается."""
    tournament = await session.get(Tournament, match.tournament_id)
    if match.stage == MatchStage.playoff:
        await move_to_next(session, match, match.winner_team_id)
    elif tournament.format == TournamentFormat.mixed and not await unfinished_count(
        session, tournament.id, MatchStage.group
    ):
        await fill_playoff_from_groups(session, tournament)
    if not await unfinished_count(session, tournament.id):
        tournament.status = TournamentStatus.finished
