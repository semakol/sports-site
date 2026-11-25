from datetime import UTC, datetime

import pytest

from app.models import Match
from app.models.enums import UserRole
from tests import test_protocol
from tests.conftest import TestSession
from tests.test_protocol import event, matches_of, play, start
from tests.test_tournaments import create_teams, create_tournament, generate

cup_factory = test_protocol.make_cup


async def test_draft_visibility(client, make_user, make_team):
    _, owner = await make_user(UserRole.organizer)
    _, other = await make_user(UserRole.organizer)
    cup = await create_tournament(client, owner)
    tid = cup["id"]
    teams = await create_teams(client, make_user, make_team, 2)
    await client.post(f"/api/tournaments/{tid}/teams", json={"team_ids": teams}, headers=owner)
    [match] = (await generate(client, owner, tid)).json()
    urls = [
        f"/api/tournaments/{tid}{suffix}"
        for suffix in ("", "/groups", "/teams", "/matches", "/bracket", "/standings", "/player-stats")
    ]
    urls += [f"/api/matches/{match['id']}{suffix}" for suffix in ("", "/events")]
    for url in urls:
        assert (await client.get(url)).status_code == 404, url
        assert (await client.get(url, headers=other)).status_code == 404, url
        assert (await client.get(url, headers=owner)).status_code == 200, url
    assert (await client.get("/api/matches")).json() == {"items": [], "total": 0}
    await client.post(f"/api/tournaments/{tid}/publish", headers=owner)
    for url in urls:
        assert (await client.get(url)).status_code == 200, url


async def test_feed_filters(client, cup_factory):
    cup = await cup_factory(teams=3, format="round_robin")
    matches = await matches_of(client, cup)
    async with TestSession() as session:
        for index, match in enumerate(matches):
            obj = await session.get(Match, match["id"])
            obj.scheduled_at = datetime(2026, 12, 5 + index, 23, 59, 59, tzinfo=UTC)
        await session.commit()
    all_items = (await client.get("/api/matches")).json()
    assert all_items["total"] == 3
    page = (await client.get("/api/matches", params={"limit": 1, "offset": 1})).json()
    assert page["total"] == 3 and page["items"][0]["id"] == all_items["items"][1]["id"]
    found = (
        await client.get(
            "/api/matches",
            params={
                "tournament_id": cup.id,
                "date_from": "2026-12-05",
                "date_to": "2026-12-05",
                "status": "scheduled,live",
                "team_id": matches[0]["away_team"]["id"],
            },
        )
    ).json()
    assert found["total"] == 1 and found["items"][0]["id"] == matches[0]["id"]
    assert (await client.get("/api/matches", params={"status": "finished"})).json()["total"] == 0
    mine = await client.get("/api/matches", params={"curator": "me"}, headers=cup.curator)
    assert mine.json()["total"] == 3
    assert (await client.get("/api/matches", params={"curator": "me"})).status_code == 401
    assert (
        await client.get("/api/matches", params={"curator": "me"}, headers=cup.organizer)
    ).status_code == 403


@pytest.mark.parametrize(
    "params",
    [
        {"status": "bad"},
        {"status": "live,"},
        {"limit": 0},
        {"offset": -1},
        {"date_from": "2026-12-06", "date_to": "2026-12-05"},
        {"curator": "someone"},
    ],
)
async def test_feed_validation(client, params):
    assert (await client.get("/api/matches", params=params)).status_code == 400


async def test_group_tables(client, cup_factory):
    cup = await cup_factory(teams=4, format="round_robin", groups=2)
    matches = await matches_of(client, cup)
    url = f"/api/tournaments/{cup.id}/standings"
    before = (await client.get(url)).json()
    assert len(before) == 2 and all(r["played"] == 0 for g in before for r in g["rows"])
    match = matches[0]
    await play(client, cup, match, 2, 0)
    table = (await client.get(url)).json()
    rows = {r["team"]["id"]: r for g in table for r in g["rows"]}
    home, away = match["home_team"]["id"], match["away_team"]["id"]
    assert (rows[home]["points"], rows[home]["won"], rows[home]["goals_for"]) == (3, 1, 2)
    assert (rows[away]["points"], rows[away]["lost"], rows[away]["goals_against"]) == (0, 1, 2)
    await play(client, cup, matches[1], 1, 1)
    table = (await client.get(url)).json()
    other = next(g for g in table if g["group"]["id"] == matches[1]["group"]["id"])
    assert all(r["drawn"] == 1 and r["points"] == 1 for r in other["rows"])


async def test_player_stats(client, cup_factory):
    cup = await cup_factory()
    [match] = await matches_of(client, cup)
    await start(client, cup, match)
    p = cup.players[match["home_team"]["id"]][0]
    goal = await event(client, cup, match["id"], "goal", p)
    await event(client, cup, match["id"], "own_goal", p)
    await event(client, cup, match["id"], "yellow_card", p)
    url = f"/api/tournaments/{cup.id}/player-stats"
    response = await client.get(url)
    assert response.status_code == 200, response.text
    row = response.json()[0]
    assert row["player"]["id"] == p and row["goals"] == 1 and row["yellow_cards"] == 1
    assert row["matches"] == 1 and "birth_date" not in row["player"]
    deleted = await client.delete(
        f"/api/matches/{match['id']}/events/{goal.json()['event']['id']}", headers=cup.curator
    )
    assert deleted.status_code == 200
    rows = (await client.get(url, params={"sort": "yellow_cards", "limit": 1})).json()
    assert len(rows) == 1 and rows[0]["goals"] == 0 and rows[0]["yellow_cards"] == 1
    assert (await client.get(url, params={"sort": "invalid"})).status_code == 400
    assert (await client.get(f"/api/tournaments/{cup.id}/standings")).json() == []


async def test_missing(client):
    for path in ("/api/tournaments/999/standings", "/api/tournaments/999/player-stats", "/api/matches/999"):
        assert (await client.get(path)).status_code == 404
