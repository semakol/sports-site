from datetime import date

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Conflict, Forbidden, NotFound
from app.models import Player, Team, TeamPlayer, TournamentTeam, User
from app.schemas.team import RosterEntry, TeamCreate, TeamRead, TeamUpdate, UserShort

ACTIVE = TeamPlayer.left_at.is_(None)

players_count = (
    select(func.count()).where(TeamPlayer.team_id == Team.id, ACTIVE).correlate(Team).scalar_subquery()
)


def team_query() -> Select:
    return select(Team, User, players_count).join(User, Team.representative_id == User.id)


def to_read(row) -> TeamRead:
    team, representative, count = row
    return TeamRead(
        id=team.id,
        name=team.name,
        logo_url=team.logo_url,
        representative=UserShort.model_validate(representative),
        players_count=count,
    )


async def get_team(session: AsyncSession, team_id: int) -> Team:
    team = await session.get(Team, team_id)
    if team is None:
        raise NotFound("Команда не найдена")
    return team


async def get_own_team(session: AsyncSession, team_id: int, user: User) -> Team:
    """Команда, которой управляет пользователь, иначе 403."""
    team = await get_team(session, team_id)
    if team.representative_id != user.id:
        raise Forbidden("Управлять командой может только её представитель")
    return team


async def read_team(session: AsyncSession, team_id: int) -> TeamRead:
    row = (await session.execute(team_query().where(Team.id == team_id))).one_or_none()
    if row is None:
        raise NotFound("Команда не найдена")
    return to_read(row)


async def list_teams(
    session: AsyncSession, representative_id: int | None, search: str | None, limit: int, offset: int
) -> tuple[list[TeamRead], int]:
    query = team_query()
    if representative_id is not None:
        query = query.where(Team.representative_id == representative_id)
    if search:
        query = query.where(Team.name.ilike(f"%{search}%"))
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    rows = await session.execute(query.order_by(Team.name, Team.id).limit(limit).offset(offset))
    return [to_read(r) for r in rows], total or 0


async def create_team(session: AsyncSession, user: User, data: TeamCreate) -> TeamRead:
    team = Team(representative_id=user.id, **data.model_dump())
    session.add(team)
    await session.commit()
    return await read_team(session, team.id)


async def update_team(session: AsyncSession, user: User, team_id: int, data: TeamUpdate) -> TeamRead:
    team = await get_own_team(session, team_id, user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(team, field, value)
    await session.commit()
    return await read_team(session, team.id)


async def delete_team(session: AsyncSession, user: User, team_id: int) -> None:
    team = await get_own_team(session, team_id, user)
    in_tournament = await session.scalar(select(TournamentTeam.id).where(TournamentTeam.team_id == team.id))
    if in_tournament:
        raise Conflict("TEAM_IN_TOURNAMENT", "Команда участвует в турнире, удалить её нельзя")
    await session.delete(team)
    await session.commit()


async def roster(session: AsyncSession, team_id: int) -> list[RosterEntry]:
    await get_team(session, team_id)
    rows = await session.execute(
        select(Player, TeamPlayer.shirt_number)
        .join(TeamPlayer, TeamPlayer.player_id == Player.id)
        .where(TeamPlayer.team_id == team_id, ACTIVE)
        .order_by(Player.last_name, Player.first_name)
    )
    return [RosterEntry(player=p, shirt_number=n) for p, n in rows]


async def add_player(
    session: AsyncSession, user: User, team_id: int, player_id: int, shirt_number: int | None
) -> RosterEntry:
    team = await get_own_team(session, team_id, user)
    player = await session.get(Player, player_id)
    if player is None:
        raise NotFound("Игрок не найден")

    membership = await session.scalar(
        select(TeamPlayer).where(TeamPlayer.team_id == team.id, TeamPlayer.player_id == player.id)
    )
    if membership is None:
        session.add(TeamPlayer(team_id=team.id, player_id=player.id, shirt_number=shirt_number))
    elif membership.left_at is None:
        raise Conflict("PLAYER_ALREADY_IN_TEAM", "Игрок уже состоит в команде", field="player_id")
    else:  # игрок возвращается в команду — та же строка, история матчей не теряется
        membership.left_at = None
        membership.joined_at = date.today()
        membership.shirt_number = shirt_number
    await session.commit()
    return RosterEntry(player=player, shirt_number=shirt_number)


async def remove_player(session: AsyncSession, user: User, team_id: int, player_id: int) -> None:
    team = await get_own_team(session, team_id, user)
    membership = await session.scalar(
        select(TeamPlayer).where(TeamPlayer.team_id == team.id, TeamPlayer.player_id == player_id, ACTIVE)
    )
    if membership is None:
        raise NotFound("Игрок не состоит в команде")
    membership.left_at = date.today()
    await session.commit()
