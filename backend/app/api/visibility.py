"""Черновики и их содержимое доступны только организатору-владельцу."""

from app.api.deps import OptionalUser
from app.core.errors import NotFound
from app.db.session import SessionDep
from app.models.enums import TournamentStatus
from app.services.matches import get_match
from app.services.tournaments import get_tournament


async def visible_tournament(tournament_id: int, session: SessionDep, user: OptionalUser) -> None:
    tournament = await get_tournament(session, tournament_id)
    if tournament.status == TournamentStatus.draft and (user is None or user.id != tournament.organizer_id):
        raise NotFound("Турнир не найден")


async def visible_match(match_id: int, session: SessionDep, user: OptionalUser) -> None:
    match = await get_match(session, match_id)
    await visible_tournament(match.tournament_id, session, user)
