from datetime import UTC, datetime

from fastapi import UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, Forbidden, NotFound
from app.models import Lineup, LineupPlayer, Match, MatchEvent, Player, Team, TeamPlayer, User
from app.models.enums import EventType, MatchStatus
from app.schemas.team import PlayerCreateForm, PlayerProfile, PlayerTotals, PlayerUpdate, TeamShort
from app.services import media
from app.services.teams import ACTIVE, get_own_team

PHOTO_FOLDER = "players"


async def get_player(session: AsyncSession, player_id: int) -> Player:
    player = await session.get(Player, player_id)
    if player is None:
        raise NotFound("Игрок не найден")
    return player


async def get_editable_player(session: AsyncSession, player_id: int, user: User) -> Player:
    """Менять данные игрока может тот, кто его создал, или представитель его текущей команды."""
    player = await get_player(session, player_id)
    if player.created_by == user.id:
        return player
    represents = await session.scalar(
        select(TeamPlayer.id)
        .join(Team, Team.id == TeamPlayer.team_id)
        .where(TeamPlayer.player_id == player.id, ACTIVE, Team.representative_id == user.id)
    )
    if not represents:
        raise Forbidden("Изменять игрока может только представитель его команды")
    return player


async def search_players(
    session: AsyncSession, search: str | None, limit: int, offset: int
) -> tuple[list[Player], int]:
    query = select(Player)
    # «Иванов Пётр» — каждое слово должно найтись в фамилии, имени или отчестве
    for word in (search or "").split():
        pattern = f"%{word}%"
        query = query.where(
            or_(
                Player.last_name.ilike(pattern),
                Player.first_name.ilike(pattern),
                Player.middle_name.ilike(pattern),
            )
        )
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    players = await session.scalars(
        query.order_by(Player.last_name, Player.first_name, Player.id).limit(limit).offset(offset)
    )
    return list(players), total or 0


async def create_player(session: AsyncSession, user: User, data: PlayerCreateForm) -> Player:
    if not data.pd_consent:
        raise AppError(
            400, "VALIDATION_ERROR", "Нужно согласие на обработку персональных данных", "pd_consent"
        )
    team = await get_own_team(session, data.team_id, user) if data.team_id is not None else None

    photo_url = await media.save_photo(data.photo, PHOTO_FOLDER)
    player = Player(
        **data.model_dump(exclude={"pd_consent", "team_id", "photo"}),
        photo_url=photo_url,
        pd_consent_at=datetime.now(UTC),
        created_by=user.id,
    )
    try:
        session.add(player)
        await session.flush()
        if team is not None:
            session.add(TeamPlayer(team_id=team.id, player_id=player.id))
        await session.commit()
    except Exception:
        media.delete_media(photo_url)  # не оставляем на диске фото без игрока
        raise
    return player


async def update_player(session: AsyncSession, user: User, player_id: int, data: PlayerUpdate) -> Player:
    player = await get_editable_player(session, player_id, user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(player, field, value)
    await session.commit()
    return player


async def replace_photo(session: AsyncSession, user: User, player_id: int, photo: UploadFile) -> Player:
    player = await get_editable_player(session, player_id, user)
    old_url = player.photo_url
    player.photo_url = await media.save_photo(photo, PHOTO_FOLDER)
    await session.commit()
    media.delete_media(old_url)
    return player


async def player_profile(session: AsyncSession, player_id: int) -> PlayerProfile:
    player = await get_player(session, player_id)
    teams = await session.scalars(
        select(Team)
        .join(TeamPlayer, TeamPlayer.team_id == Team.id)
        .where(TeamPlayer.player_id == player.id, ACTIVE)
        .order_by(Team.name)
    )
    # В статистику идут только завершённые матчи и неотменённые события
    matches = await session.scalar(
        select(func.count())
        .select_from(LineupPlayer)
        .join(Lineup, Lineup.id == LineupPlayer.lineup_id)
        .join(Match, Match.id == Lineup.match_id)
        .where(LineupPlayer.player_id == player.id, Match.status == MatchStatus.finished)
    )
    counts = dict(
        (
            await session.execute(
                select(MatchEvent.type, func.count())
                .where(MatchEvent.player_id == player.id, MatchEvent.cancelled_at.is_(None))
                .group_by(MatchEvent.type)
            )
        ).all()
    )
    totals = PlayerTotals(
        matches=matches or 0,
        goals=counts.get(EventType.goal, 0),
        yellow_cards=counts.get(EventType.yellow_card, 0),
        red_cards=counts.get(EventType.red_card, 0),
    )
    return PlayerProfile(
        id=player.id,
        last_name=player.last_name,
        first_name=player.first_name,
        middle_name=player.middle_name,
        photo_url=player.photo_url,
        teams=[TeamShort.model_validate(t) for t in teams],
        totals=totals,
    )
