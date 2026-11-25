"""Публичная таблица и статистика считаются из актуальных результатов и событий."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lineup, LineupPlayer, Match, MatchEvent, Player, Team, TournamentGroup, TournamentTeam
from app.models.enums import EventType, MatchStage, MatchStatus, TournamentFormat
from app.schemas.team import PlayerShort, TeamShort
from app.schemas.tournament import GroupShort, GroupStandings, PlayerStatRow, StandingRow
from app.services.tournaments import get_tournament


async def standings(session: AsyncSession, tournament_id: int) -> list[GroupStandings]:
    tournament = await get_tournament(session, tournament_id)
    if tournament.format == TournamentFormat.playoff:
        return []
    groups = list(
        await session.scalars(
            select(TournamentGroup)
            .where(TournamentGroup.tournament_id == tournament_id)
            .order_by(TournamentGroup.name, TournamentGroup.id)
        )
    )
    entries = list(
        await session.execute(
            select(TournamentTeam, Team)
            .join(Team, Team.id == TournamentTeam.team_id)
            .where(TournamentTeam.tournament_id == tournament_id)
        )
    )
    rows = {team.id: StandingRow(team=TeamShort.model_validate(team)) for entry, team in entries}
    matches = await session.scalars(
        select(Match).where(
            Match.tournament_id == tournament_id,
            Match.stage == MatchStage.group,
            Match.status == MatchStatus.finished,
        )
    )
    for match in matches:
        for team_id, scored, conceded in (
            (match.home_team_id, match.home_score, match.away_score),
            (match.away_team_id, match.away_score, match.home_score),
        ):
            if team_id not in rows:
                continue
            row = rows[team_id]
            row.played += 1
            row.goals_for += scored
            row.goals_against += conceded
            if scored > conceded:
                row.won += 1
                row.points += tournament.points_win
            elif scored == conceded:
                row.drawn += 1
                row.points += tournament.points_draw
            else:
                row.lost += 1
    result = []
    buckets = [(g.id, GroupShort.model_validate(g)) for g in groups]
    if not groups or any(entry.group_id is None for entry, _ in entries):
        buckets.append((None, None))
    for group_id, group in buckets:
        table = [rows[team.id] for entry, team in entries if entry.group_id == group_id]
        table.sort(key=lambda r: (-r.points, -(r.goals_for - r.goals_against), -r.goals_for, r.team.id))
        for position, row in enumerate(table, 1):
            row.position = position
        result.append(GroupStandings(group=group, rows=table))
    return result


async def player_stats(
    session: AsyncSession,
    tournament_id: int,
    sort: str,
    limit: int,
) -> list[PlayerStatRow]:
    await get_tournament(session, tournament_id)
    types = {
        "goals": EventType.goal,
        "yellow_cards": EventType.yellow_card,
        "red_cards": EventType.red_card,
    }
    counts = {key: func.count().filter(MatchEvent.type == value).label(key) for key, value in types.items()}
    totals = (
        select(MatchEvent.player_id, MatchEvent.team_id, *counts.values())
        .join(Match, Match.id == MatchEvent.match_id)
        .where(
            Match.tournament_id == tournament_id,
            Match.status.in_((MatchStatus.live, MatchStatus.finished)),
            MatchEvent.cancelled_at.is_(None),
            MatchEvent.type.in_(types.values()),
        )
        .group_by(MatchEvent.player_id, MatchEvent.team_id)
        .subquery()
    )
    appearances = (
        select(LineupPlayer.player_id, Lineup.team_id, func.count().label("matches"))
        .join(Lineup, Lineup.id == LineupPlayer.lineup_id)
        .join(Match, Match.id == Lineup.match_id)
        .where(
            Match.tournament_id == tournament_id, Match.status.in_((MatchStatus.live, MatchStatus.finished))
        )
        .group_by(LineupPlayer.player_id, Lineup.team_id)
        .subquery()
    )
    # Включаем заявленных игроков с нулевыми показателями, сохраняем команду на момент матча.
    rows = await session.execute(
        select(Player, Team, appearances.c.matches, *(func.coalesce(totals.c[key], 0) for key in counts))
        .join(appearances, appearances.c.player_id == Player.id)
        .join(Team, Team.id == appearances.c.team_id)
        .outerjoin(totals, (totals.c.player_id == Player.id) & (totals.c.team_id == Team.id))
        .order_by(func.coalesce(totals.c[sort], 0).desc(), Player.id, Team.id)
        .limit(limit)
    )
    return [
        PlayerStatRow(
            player=PlayerShort.model_validate(player),
            team=TeamShort.model_validate(team),
            matches=matches,
            **dict(zip(counts, values, strict=True)),
        )
        for player, team, matches, *values in rows
    ]
