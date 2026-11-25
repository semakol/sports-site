from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Conflict, Forbidden, NotFound
from app.models import Match, Team, Tournament, TournamentGroup, TournamentTeam, User
from app.models.enums import TournamentFormat, TournamentStatus
from app.schemas.team import TeamShort, UserShort
from app.schemas.tournament import (
    GroupRead,
    GroupShort,
    TournamentCreate,
    TournamentRead,
    TournamentTeamRead,
    TournamentTeamsAdd,
    TournamentTeamUpdate,
    TournamentUpdate,
)

teams_count = (
    select(func.count())
    .where(TournamentTeam.tournament_id == Tournament.id)
    .correlate(Tournament)
    .scalar_subquery()
)


def tournament_query() -> Select:
    return select(Tournament, User, teams_count).join(User, Tournament.organizer_id == User.id)


def to_read(row) -> TournamentRead:
    tournament, organizer, count = row
    return TournamentRead.model_validate(
        {**tournament.__dict__, "organizer": UserShort.model_validate(organizer), "teams_count": count}
    )


async def get_tournament(session: AsyncSession, tournament_id: int) -> Tournament:
    tournament = await session.get(Tournament, tournament_id)
    if tournament is None:
        raise NotFound("Турнир не найден")
    return tournament


async def get_own_tournament(session: AsyncSession, tournament_id: int, user: User) -> Tournament:
    """Турнир, который ведёт пользователь, иначе 403."""
    tournament = await get_tournament(session, tournament_id)
    if tournament.organizer_id != user.id:
        raise Forbidden("Управлять турниром может только его организатор")
    return tournament


def ensure_draft(tournament: Tournament) -> None:
    if tournament.status != TournamentStatus.draft:
        raise Conflict("TOURNAMENT_NOT_DRAFT", "Турнир уже опубликован, менять его нельзя")


async def has_schedule(session: AsyncSession, tournament_id: int) -> bool:
    return bool(await session.scalar(select(Match.id).where(Match.tournament_id == tournament_id).limit(1)))


async def ensure_structure_editable(session: AsyncSession, tournament: Tournament) -> None:
    """Группы и участников можно менять только в черновике и до генерации расписания."""
    ensure_draft(tournament)
    if await has_schedule(session, tournament.id):
        raise Conflict("SCHEDULE_GENERATED", "Расписание уже создано — сначала удалите его")


async def read_tournament(session: AsyncSession, tournament_id: int) -> TournamentRead:
    row = (await session.execute(tournament_query().where(Tournament.id == tournament_id))).one_or_none()
    if row is None:
        raise NotFound("Турнир не найден")
    return to_read(row)


async def list_tournaments(
    session: AsyncSession,
    organizer_id: int | None,
    status: TournamentStatus | None,
    limit: int,
    offset: int,
) -> tuple[list[TournamentRead], int]:
    query = tournament_query()
    if organizer_id is not None:
        query = query.where(Tournament.organizer_id == organizer_id)
    else:  # черновики видит только их организатор
        query = query.where(Tournament.status != TournamentStatus.draft)
    if status is not None:
        query = query.where(Tournament.status == status)
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    rows = await session.execute(
        query.order_by(Tournament.start_date.desc(), Tournament.id.desc()).limit(limit).offset(offset)
    )
    return [to_read(r) for r in rows], total or 0


async def create_tournament(session: AsyncSession, user: User, data: TournamentCreate) -> TournamentRead:
    tournament = Tournament(organizer_id=user.id, **data.model_dump())
    session.add(tournament)
    await session.commit()
    return await read_tournament(session, tournament.id)


async def update_tournament(
    session: AsyncSession, user: User, tournament_id: int, data: TournamentUpdate
) -> TournamentRead:
    tournament = await get_own_tournament(session, tournament_id, user)
    changes = data.model_dump(exclude_unset=True)
    ensure_draft(tournament)
    if "format" in changes and changes["format"] != tournament.format:
        await ensure_structure_editable(session, tournament)
    start = changes.get("start_date", tournament.start_date)
    end = changes.get("end_date", tournament.end_date)
    if end < start:
        raise Conflict("INVALID_DATES", "Дата окончания раньше даты начала", field="end_date")
    for field, value in changes.items():
        setattr(tournament, field, value)
    await session.commit()
    return await read_tournament(session, tournament.id)


async def delete_tournament(session: AsyncSession, user: User, tournament_id: int) -> None:
    tournament = await get_own_tournament(session, tournament_id, user)
    ensure_draft(tournament)
    await session.delete(tournament)
    await session.commit()


async def publish(session: AsyncSession, user: User, tournament_id: int) -> TournamentRead:
    tournament = await get_own_tournament(session, tournament_id, user)
    ensure_draft(tournament)
    if not await has_schedule(session, tournament.id):
        raise Conflict("SCHEDULE_NOT_GENERATED", "Перед публикацией сгенерируйте расписание")
    tournament.status = TournamentStatus.published
    await session.commit()
    return await read_tournament(session, tournament.id)


# ─── группы ───
async def get_group(session: AsyncSession, tournament_id: int, group_id: int) -> TournamentGroup:
    group = await session.get(TournamentGroup, group_id)
    if group is None or group.tournament_id != tournament_id:
        raise NotFound("Группа не найдена")
    return group


async def list_groups(session: AsyncSession, tournament_id: int) -> list[GroupRead]:
    await get_tournament(session, tournament_id)
    groups = (
        await session.scalars(
            select(TournamentGroup)
            .where(TournamentGroup.tournament_id == tournament_id)
            .order_by(TournamentGroup.name, TournamentGroup.id)
        )
    ).all()
    rows = await session.execute(
        select(TournamentTeam.group_id, Team)
        .join(Team, Team.id == TournamentTeam.team_id)
        .where(TournamentTeam.tournament_id == tournament_id, TournamentTeam.group_id.is_not(None))
        .order_by(TournamentTeam.seed.nulls_last(), Team.name)
    )
    teams: dict[int, list[TeamShort]] = {}
    for group_id, team in rows:
        teams.setdefault(group_id, []).append(TeamShort.model_validate(team))
    return [GroupRead(id=g.id, name=g.name, teams=teams.get(g.id, [])) for g in groups]


async def create_group(session: AsyncSession, user: User, tournament_id: int, name: str) -> GroupRead:
    tournament = await get_own_tournament(session, tournament_id, user)
    await ensure_structure_editable(session, tournament)
    if tournament.format == TournamentFormat.playoff:
        raise Conflict("GROUPS_NOT_ALLOWED", "В турнире на выбывание нет групп")
    taken = await session.scalar(
        select(TournamentGroup.id).where(
            TournamentGroup.tournament_id == tournament.id, TournamentGroup.name == name
        )
    )
    if taken:
        raise Conflict("GROUP_NAME_TAKEN", "Группа с таким названием уже есть", field="name")
    group = TournamentGroup(tournament_id=tournament.id, name=name)
    session.add(group)
    await session.commit()
    return GroupRead(id=group.id, name=group.name, teams=[])


async def delete_group(session: AsyncSession, user: User, tournament_id: int, group_id: int) -> None:
    tournament = await get_own_tournament(session, tournament_id, user)
    await ensure_structure_editable(session, tournament)
    group = await get_group(session, tournament.id, group_id)
    await session.delete(group)  # команды остаются в турнире без группы (ON DELETE SET NULL)
    await session.commit()


# ─── участники ───
async def list_teams(session: AsyncSession, tournament_id: int) -> list[TournamentTeamRead]:
    await get_tournament(session, tournament_id)
    rows = await session.execute(
        select(TournamentTeam, Team, TournamentGroup)
        .join(Team, Team.id == TournamentTeam.team_id)
        .outerjoin(TournamentGroup, TournamentGroup.id == TournamentTeam.group_id)
        .where(TournamentTeam.tournament_id == tournament_id)
        .order_by(TournamentGroup.name.nulls_last(), TournamentTeam.seed.nulls_last(), Team.name)
    )
    return [
        TournamentTeamRead(
            team=TeamShort.model_validate(team),
            group=GroupShort.model_validate(group) if group else None,
            seed=entry.seed,
        )
        for entry, team, group in rows
    ]


async def check_group(session: AsyncSession, tournament: Tournament, group_id: int | None) -> None:
    if group_id is None:
        return
    group = await session.get(TournamentGroup, group_id)
    if group is None or group.tournament_id != tournament.id:
        raise NotFound("Группа не найдена")


async def add_teams(
    session: AsyncSession, user: User, tournament_id: int, data: TournamentTeamsAdd
) -> list[TournamentTeamRead]:
    tournament = await get_own_tournament(session, tournament_id, user)
    await ensure_structure_editable(session, tournament)
    await check_group(session, tournament, data.group_id)
    team_ids = list(dict.fromkeys(data.team_ids))

    found = set(await session.scalars(select(Team.id).where(Team.id.in_(team_ids))))
    if missing := [i for i in team_ids if i not in found]:
        raise NotFound(f"Команда {missing[0]} не найдена")
    already = await session.scalar(
        select(TournamentTeam.team_id).where(
            TournamentTeam.tournament_id == tournament.id, TournamentTeam.team_id.in_(team_ids)
        )
    )
    if already:
        raise Conflict("TEAM_ALREADY_IN_TOURNAMENT", "Команда уже участвует в турнире", field="team_ids")

    session.add_all(
        TournamentTeam(tournament_id=tournament.id, team_id=i, group_id=data.group_id) for i in team_ids
    )
    await session.commit()
    return [e for e in await list_teams(session, tournament.id) if e.team.id in found]


async def get_entry(session: AsyncSession, tournament_id: int, team_id: int) -> TournamentTeam:
    entry = await session.scalar(
        select(TournamentTeam).where(
            TournamentTeam.tournament_id == tournament_id, TournamentTeam.team_id == team_id
        )
    )
    if entry is None:
        raise NotFound("Команда не участвует в турнире")
    return entry


async def update_team(
    session: AsyncSession, user: User, tournament_id: int, team_id: int, data: TournamentTeamUpdate
) -> TournamentTeamRead:
    tournament = await get_own_tournament(session, tournament_id, user)
    await ensure_structure_editable(session, tournament)
    entry = await get_entry(session, tournament.id, team_id)
    changes = data.model_dump(exclude_unset=True)
    if "group_id" in changes:
        await check_group(session, tournament, changes["group_id"])
    for field, value in changes.items():
        setattr(entry, field, value)
    await session.commit()
    return next(e for e in await list_teams(session, tournament.id) if e.team.id == team_id)


async def remove_team(session: AsyncSession, user: User, tournament_id: int, team_id: int) -> None:
    tournament = await get_own_tournament(session, tournament_id, user)
    await ensure_structure_editable(session, tournament)
    entry = await get_entry(session, tournament.id, team_id)
    await session.delete(entry)
    await session.commit()


async def delete_schedule(session: AsyncSession, user: User, tournament_id: int) -> None:
    """Удалить расписание черновика, чтобы поменять группы или участников и сгенерировать заново."""
    tournament = await get_own_tournament(session, tournament_id, user)
    ensure_draft(tournament)
    await session.execute(delete(Match).where(Match.tournament_id == tournament.id))
    await session.commit()
