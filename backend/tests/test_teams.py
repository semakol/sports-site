from datetime import date

from app.models import Tournament, TournamentTeam
from app.models.enums import TournamentFormat, UserRole
from tests.conftest import TestSession


async def test_team_rep_creates_team(client, make_user):
    rep, headers = await make_user(UserRole.team_rep)

    response = await client.post("/api/teams", json={"name": "  Уралмаш  "}, headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Уралмаш"
    assert body["representative"] == {"id": rep.id, "full_name": rep.full_name}
    assert body["players_count"] == 0


async def test_only_team_rep_creates_team(client, make_user):
    _, headers = await make_user(UserRole.organizer)

    assert (await client.post("/api/teams", json={"name": "X"}, headers=headers)).status_code == 403
    assert (await client.post("/api/teams", json={"name": "X"})).status_code == 401


async def test_list_teams_is_public_and_mine_filters(client, make_user, make_team):
    _, rep1 = await make_user()
    _, rep2 = await make_user()
    await make_team(rep1, "Уралмаш")
    await make_team(rep2, "Синара")

    public = await client.get("/api/teams", params={"search": "урал"})
    mine = await client.get("/api/teams", params={"mine": "true"}, headers=rep2)

    assert public.json()["total"] == 1 and public.json()["items"][0]["name"] == "Уралмаш"
    assert [t["name"] for t in mine.json()["items"]] == ["Синара"]


async def test_mine_requires_auth(client):
    response = await client.get("/api/teams", params={"mine": "true"})

    assert response.status_code == 401


async def test_only_representative_updates_team(client, make_user, make_team):
    _, owner = await make_user()
    _, other = await make_user()
    team = await make_team(owner)

    forbidden = await client.patch(f"/api/teams/{team['id']}", json={"name": "Чужая"}, headers=other)
    updated = await client.patch(f"/api/teams/{team['id']}", json={"logo_url": "/logo.png"}, headers=owner)

    assert forbidden.status_code == 403
    assert updated.status_code == 200
    assert updated.json()["name"] == "Уралмаш"
    assert updated.json()["logo_url"] == "/logo.png"


async def test_team_name_cannot_be_nulled(client, make_user, make_team):
    _, owner = await make_user()
    team = await make_team(owner)

    response = await client.patch(f"/api/teams/{team['id']}", json={"name": None}, headers=owner)

    assert response.status_code == 400
    assert response.json()["field"] == "name"


async def test_delete_team(client, make_user, make_team):
    _, owner = await make_user()
    team = await make_team(owner)

    assert (await client.delete(f"/api/teams/{team['id']}", headers=owner)).status_code == 204
    assert (await client.get(f"/api/teams/{team['id']}")).status_code == 404


async def test_team_in_tournament_cannot_be_deleted(client, make_user, make_team):
    organizer, _ = await make_user(UserRole.organizer)
    _, owner = await make_user()
    team = await make_team(owner)
    async with TestSession() as session:
        tournament = Tournament(
            organizer_id=organizer.id,
            name="Кубок",
            format=TournamentFormat.round_robin,
            start_date=date(2026, 11, 1),
            end_date=date(2026, 12, 1),
        )
        session.add(tournament)
        await session.flush()
        session.add(TournamentTeam(tournament_id=tournament.id, team_id=team["id"]))
        await session.commit()

    response = await client.delete(f"/api/teams/{team['id']}", headers=owner)

    assert response.status_code == 409
    assert response.json()["code"] == "TEAM_IN_TOURNAMENT"


async def test_roster_add_remove_and_rejoin(client, make_user, make_team, make_player):
    _, owner = await make_user()
    team = await make_team(owner)
    player = await make_player(owner)
    url = f"/api/teams/{team['id']}/players"

    added = await client.post(url, json={"player_id": player["id"], "shirt_number": 10}, headers=owner)
    duplicate = await client.post(url, json={"player_id": player["id"]}, headers=owner)
    roster = await client.get(url)

    assert added.status_code == 201
    assert duplicate.status_code == 409 and duplicate.json()["code"] == "PLAYER_ALREADY_IN_TEAM"
    assert [(e["player"]["id"], e["shirt_number"]) for e in roster.json()] == [(player["id"], 10)]
    assert (await client.get(f"/api/teams/{team['id']}")).json()["players_count"] == 1

    removed = await client.delete(f"{url}/{player['id']}", headers=owner)
    assert removed.status_code == 204
    assert (await client.get(url)).json() == []

    rejoined = await client.post(url, json={"player_id": player["id"], "shirt_number": 7}, headers=owner)
    assert rejoined.status_code == 201
    assert (await client.get(url)).json()[0]["shirt_number"] == 7


async def test_only_representative_manages_roster(client, make_user, make_team, make_player):
    _, owner = await make_user()
    _, other = await make_user()
    team = await make_team(owner)
    player = await make_player(other)

    response = await client.post(
        f"/api/teams/{team['id']}/players", json={"player_id": player["id"]}, headers=other
    )

    assert response.status_code == 403


async def test_add_unknown_player_returns_404(client, make_user, make_team):
    _, owner = await make_user()
    team = await make_team(owner)

    response = await client.post(f"/api/teams/{team['id']}/players", json={"player_id": 999}, headers=owner)

    assert response.status_code == 404
