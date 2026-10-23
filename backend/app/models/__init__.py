"""ORM-модели. Каждую новую модель импортируйте здесь, чтобы Alembic увидел её при autogenerate."""

from app.models.match import Lineup, LineupPlayer, Match, MatchEvent, MatchPeriod
from app.models.team import Player, Team, TeamPlayer
from app.models.tournament import Standing, Tournament, TournamentGroup, TournamentTeam
from app.models.user import User

__all__ = [
    "Lineup",
    "LineupPlayer",
    "Match",
    "MatchEvent",
    "MatchPeriod",
    "Player",
    "Standing",
    "Team",
    "TeamPlayer",
    "Tournament",
    "TournamentGroup",
    "TournamentTeam",
    "User",
]
