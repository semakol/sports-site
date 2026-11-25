from collections import Counter
from itertools import combinations

from app.models.enums import UserRole

FIRST_ROUND = "2026-12-05T10:00:00+05:00"


def tournament_form(**overrides) -> dict:
    form = {
        "name": "Кубок УрФУ",
        "format": "round_robin",
        "start_date": "2026-12-01",
        "end_date": "2026-12-31",
    }
    return {**form, **overrides}


async def create_tournament(client, headers, **overrides) -> dict:
    response = await client.post("/api/tournaments", json=tournament_form(**overrides), headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


async def create_teams(client, make_user, make_team, count: int) -> list[int]:
    _, rep = await make_user()
    return [(await make_team(rep, f"Команда {i + 1}"))["id"] for i in range(count)]


async def add_group(client, headers, tournament_id, name, team_ids) -> dict:
    group = await client.post(
        f"/api/tournaments/{tournament_id}/groups", json={"name": name}, headers=headers
    )
    assert group.status_code == 201, group.text
    added = await client.post(
        f"/api/tournaments/{tournament_id}/teams",
        json={"team_ids": team_ids, "group_id": group.json()["id"]},
        headers=headers,
    )
    assert added.status_code == 201, added.text
    return group.json()


async def generate(client, headers, tournament_id, **body):
    return await client.post(
        f"/api/tournaments/{tournament_id}/schedule",
        json={"first_round_at": FIRST_ROUND, **body},
        headers=headers,
    )


async def test_organizer_creates_draft(client, make_user):
    organizer, headers = await make_user(UserRole.organizer)
    _, rep = await make_user()

    tournament = await create_tournament(client, headers)

    assert tournament["status"] == "draft"
    assert tournament["organizer"]["id"] == organizer.id
    assert tournament["teams_count"] == 0 and tournament["points_win"] == 3
    assert (await client.post("/api/tournaments", json=tournament_form(), headers=rep)).status_code == 403
    assert (await client.get("/api/tournaments")).json()["total"] == 0  # черновики не публичны
    mine = await client.get("/api/tournaments", params={"mine": "true"}, headers=headers)
    assert [t["id"] for t in mine.json()["items"]] == [tournament["id"]]


async def test_end_date_before_start_is_rejected(client, make_user):
    _, headers = await make_user(UserRole.organizer)

    response = await client.post(
        "/api/tournaments", json=tournament_form(end_date="2026-11-01"), headers=headers
    )

    assert response.status_code == 400


async def test_only_owner_manages_tournament(client, make_user):
    _, owner = await make_user(UserRole.organizer)
    _, other = await make_user(UserRole.organizer)
    tournament = await create_tournament(client, owner)
    url = f"/api/tournaments/{tournament['id']}"

    assert (await client.patch(url, json={"name": "Чужой"}, headers=other)).status_code == 403
    assert (await client.post(f"{url}/groups", json={"name": "A"}, headers=other)).status_code == 403
    assert (await client.patch(url, json={"name": "Весенний"}, headers=owner)).json()["name"] == "Весенний"


async def test_groups_and_participants(client, make_user, make_team):
    _, headers = await make_user(UserRole.organizer)
    tournament = await create_tournament(client, headers)
    teams = await create_teams(client, make_user, make_team, 3)
    url = f"/api/tournaments/{tournament['id']}"

    group = await add_group(client, headers, tournament["id"], "A", teams[:2])
    duplicate_name = await client.post(f"{url}/groups", json={"name": "A"}, headers=headers)
    duplicate_team = await client.post(f"{url}/teams", json={"team_ids": [teams[0]]}, headers=headers)
    await client.post(f"{url}/teams", json={"team_ids": [teams[2]]}, headers=headers)

    assert duplicate_name.status_code == 409 and duplicate_name.json()["code"] == "GROUP_NAME_TAKEN"
    assert duplicate_team.status_code == 409 and duplicate_team.json()["code"] == "TEAM_ALREADY_IN_TOURNAMENT"
    groups = (await client.get(f"{url}/groups", headers=headers)).json()
    assert [(g["name"], [t["id"] for t in g["teams"]]) for g in groups] == [("A", teams[:2])]
    assert (await client.get(url, headers=headers)).json()["teams_count"] == 3

    moved = await client.patch(f"{url}/teams/{teams[2]}", json={"group_id": group["id"]}, headers=headers)
    assert moved.json()["group"] == {"id": group["id"], "name": "A"}

    assert (await client.delete(f"{url}/groups/{group['id']}", headers=headers)).status_code == 204
    participants = (await client.get(f"{url}/teams", headers=headers)).json()
    assert len(participants) == 3 and all(p["group"] is None for p in participants)


async def test_playoff_has_no_groups(client, make_user):
    _, headers = await make_user(UserRole.organizer)
    tournament = await create_tournament(client, headers, format="playoff")

    response = await client.post(
        f"/api/tournaments/{tournament['id']}/groups", json={"name": "A"}, headers=headers
    )

    assert response.status_code == 409 and response.json()["code"] == "GROUPS_NOT_ALLOWED"


async def test_round_robin_in_groups(client, make_user, make_team):
    _, headers = await make_user(UserRole.organizer)
    tournament = await create_tournament(client, headers)
    teams = await create_teams(client, make_user, make_team, 7)
    a = await add_group(client, headers, tournament["id"], "A", teams[:4])
    b = await add_group(client, headers, tournament["id"], "B", teams[4:])

    response = await generate(client, headers, tournament["id"], days_between_rounds=7, venue="Манеж")

    assert response.status_code == 201
    matches = response.json()
    by_group = Counter(m["group"]["id"] for m in matches)
    assert by_group == {a["id"]: 6, b["id"]: 3}
    for group_teams in (teams[:4], teams[4:]):
        pairs = {
            frozenset((m["home_team"]["id"], m["away_team"]["id"]))
            for m in matches
            if m["home_team"]["id"] in group_teams
        }
        assert pairs == {frozenset(p) for p in combinations(group_teams, 2)}  # каждая пара ровно один раз
    # в туре команда играет не больше одного раза
    for round_ in {m["round"] for m in matches}:
        playing = [
            t for m in matches if m["round"] == round_ for t in (m["home_team"]["id"], m["away_team"]["id"])
        ]
        assert len(playing) == len(set(playing))
    assert {m["scheduled_at"][:10] for m in matches} == {"2026-12-05", "2026-12-12", "2026-12-19"}
    assert all(m["stage"] == "group" and m["venue"] == "Манеж" for m in matches)


async def test_all_teams_must_have_group(client, make_user, make_team):
    _, headers = await make_user(UserRole.organizer)
    tournament = await create_tournament(client, headers)
    teams = await create_teams(client, make_user, make_team, 3)
    await add_group(client, headers, tournament["id"], "A", teams[:2])
    await client.post(
        f"/api/tournaments/{tournament['id']}/teams", json={"team_ids": [teams[2]]}, headers=headers
    )

    response = await generate(client, headers, tournament["id"])

    assert response.status_code == 409 and response.json()["code"] == "TEAMS_WITHOUT_GROUP"


async def test_playoff_bracket_with_byes(client, make_user, make_team):
    _, headers = await make_user(UserRole.organizer)
    tournament = await create_tournament(client, headers, format="playoff")
    teams = await create_teams(client, make_user, make_team, 5)
    url = f"/api/tournaments/{tournament['id']}"
    await client.post(f"{url}/teams", json={"team_ids": teams}, headers=headers)
    for seed, team_id in enumerate(teams, start=1):
        await client.patch(f"{url}/teams/{team_id}", json={"seed": seed}, headers=headers)

    assert (await generate(client, headers, tournament["id"])).status_code == 201
    bracket = (await client.get(f"{url}/bracket", headers=headers)).json()

    assert [r["name"] for r in bracket] == ["1/4 финала", "1/2 финала", "Финал"]

    def ids(match):
        return [
            match["home_team"] and match["home_team"]["id"],
            match["away_team"] and match["away_team"]["id"],
        ]

    quarter, semis, final = (r["matches"] for r in bracket)
    # у 5 команд сетка на 8 мест: посев 1–3 пропускает первый раунд, 4-й играет с 5-м
    assert [ids(m) for m in quarter] == [[teams[3], teams[4]]]
    assert [ids(m) for m in semis] == [[teams[0], None], [teams[1], teams[2]]]
    assert ids(final[0]) == [None, None]
    assert quarter[0]["next_match_id"] == semis[0]["id"]
    assert {m["next_match_id"] for m in semis} == {final[0]["id"]}
    assert [m["scheduled_at"][:10] for m in (quarter[0], semis[0], final[0])] == [
        "2026-12-05",
        "2026-12-12",
        "2026-12-19",
    ]


async def test_mixed_creates_groups_and_empty_bracket(client, make_user, make_team):
    _, headers = await make_user(UserRole.organizer)
    tournament = await create_tournament(client, headers, format="mixed", advance_per_group=2)
    teams = await create_teams(client, make_user, make_team, 6)
    await add_group(client, headers, tournament["id"], "A", teams[:3])
    await add_group(client, headers, tournament["id"], "B", teams[3:])

    matches = (await generate(client, headers, tournament["id"])).json()

    group_matches = [m for m in matches if m["stage"] == "group"]
    playoff = [m for m in matches if m["stage"] == "playoff"]
    assert len(group_matches) == 6
    assert [(m["round"], m["home_team"], m["away_team"]) for m in playoff] == [
        (1, None, None),
        (1, None, None),
        (2, None, None),
    ]
    # плей-офф начинается после трёх туров группового этапа
    assert playoff[0]["scheduled_at"][:10] == "2026-12-26"


async def test_mixed_bracket_size_must_be_power_of_two(client, make_user, make_team):
    _, headers = await make_user(UserRole.organizer)
    tournament = await create_tournament(client, headers, format="mixed", advance_per_group=1)
    teams = await create_teams(client, make_user, make_team, 6)
    for i, name in enumerate("ABC"):
        await add_group(client, headers, tournament["id"], name, teams[2 * i : 2 * i + 2])

    response = await generate(client, headers, tournament["id"])

    assert response.status_code == 409 and response.json()["code"] == "INVALID_BRACKET_SIZE"


async def test_structure_is_locked_after_schedule(client, make_user, make_team):
    _, headers = await make_user(UserRole.organizer)
    tournament = await create_tournament(client, headers)
    teams = await create_teams(client, make_user, make_team, 3)
    url = f"/api/tournaments/{tournament['id']}"
    await client.post(f"{url}/teams", json={"team_ids": teams[:2]}, headers=headers)

    not_ready = await client.post(f"{url}/publish", headers=headers)
    assert not_ready.status_code == 409 and not_ready.json()["code"] == "SCHEDULE_NOT_GENERATED"

    await generate(client, headers, tournament["id"])
    locked = await client.post(f"{url}/teams", json={"team_ids": [teams[2]]}, headers=headers)
    again = await generate(client, headers, tournament["id"])
    assert locked.status_code == 409 and locked.json()["code"] == "SCHEDULE_GENERATED"
    assert again.status_code == 409

    assert (await client.delete(f"{url}/schedule", headers=headers)).status_code == 204
    assert (
        await client.post(f"{url}/teams", json={"team_ids": [teams[2]]}, headers=headers)
    ).status_code == 201
    assert len((await generate(client, headers, tournament["id"])).json()) == 3

    published = await client.post(f"{url}/publish", headers=headers)
    assert published.json()["status"] == "published"
    assert (await client.get("/api/tournaments")).json()["total"] == 1
    assert (await client.patch(url, json={"name": "X"}, headers=headers)).json()[
        "code"
    ] == "TOURNAMENT_NOT_DRAFT"
