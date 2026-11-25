import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import pytest

from app.models.enums import UserRole


@dataclass
class Cup:
    """Опубликованный турнир: у каждой команды свой представитель и три игрока, один из них запасной."""

    id: int
    organizer: dict
    curator: dict
    teams: list[int]
    reps: dict[int, dict] = field(default_factory=dict)
    players: dict[int, list[int]] = field(default_factory=dict)


@pytest.fixture
def make_cup(client, make_user, make_team, make_player):
    async def factory(
        teams: int = 2, format: str = "playoff", groups: int = 0, advance: int | None = None
    ) -> Cup:
        _, organizer = await make_user(UserRole.organizer)
        curator, curator_headers = await make_user(UserRole.curator)
        body = {
            "name": "Кубок",
            "format": format,
            "start_date": "2026-12-01",
            "end_date": "2026-12-31",
            "advance_per_group": advance,
        }
        tournament = (await client.post("/api/tournaments", json=body, headers=organizer)).json()
        url = f"/api/tournaments/{tournament['id']}"
        cup = Cup(tournament["id"], organizer, curator_headers, [])
        for i in range(teams):
            _, rep = await make_user()
            team_id = (await make_team(rep, f"Команда {i + 1}"))["id"]
            cup.teams.append(team_id)
            cup.reps[team_id] = rep
            cup.players[team_id] = [
                (await make_player(rep, last_name=f"Игрок{i}{n}", team_id=str(team_id)))["id"]
                for n in range(3)
            ]
        if groups:
            size = teams // groups
            for g in range(groups):
                group = await client.post(f"{url}/groups", json={"name": "ABCD"[g]}, headers=organizer)
                await client.post(
                    f"{url}/teams",
                    json={"team_ids": cup.teams[g * size : (g + 1) * size], "group_id": group.json()["id"]},
                    headers=organizer,
                )
        else:
            await client.post(f"{url}/teams", json={"team_ids": cup.teams}, headers=organizer)
            for seed, team_id in enumerate(cup.teams, start=1):
                await client.patch(f"{url}/teams/{team_id}", json={"seed": seed}, headers=organizer)

        first_round = (datetime.now(UTC) + timedelta(days=3)).isoformat()
        matches = await client.post(
            f"{url}/schedule", json={"first_round_at": first_round}, headers=organizer
        )
        assert matches.status_code == 201, matches.text
        for match in matches.json():
            await client.patch(
                f"/api/matches/{match['id']}", json={"curator_id": curator.id}, headers=organizer
            )
        assert (await client.post(f"{url}/publish", headers=organizer)).status_code == 200
        return cup

    return factory


async def matches_of(client, cup: Cup) -> list[dict]:
    return (await client.get(f"/api/tournaments/{cup.id}/matches")).json()


async def submit_lineup(client, cup: Cup, match_id: int, team_id: int):
    starting, bench = cup.players[team_id][:2], cup.players[team_id][2]
    players = [{"player_id": p, "shirt_number": n + 1, "is_starting": True} for n, p in enumerate(starting)]
    players.append({"player_id": bench, "shirt_number": 12, "is_starting": False})
    return await client.put(
        f"/api/matches/{match_id}/lineups/{team_id}", json={"players": players}, headers=cup.reps[team_id]
    )


async def start(client, cup: Cup, match: dict) -> None:
    for team in (match["home_team"], match["away_team"]):
        assert (await submit_lineup(client, cup, match["id"], team["id"])).status_code == 200
    response = await client.post(f"/api/matches/{match['id']}/start", headers=cup.curator)
    assert response.status_code == 200, response.text


async def event(
    client, cup: Cup, match_id: int, type_: str, player_id: int, player_in_id=None, event_id=None
):
    body = {
        "client_event_id": str(event_id or uuid.uuid4()),
        "type": type_,
        "player_id": player_id,
        "client_ts": datetime.now(UTC).isoformat(),
    }
    if player_in_id is not None:
        body["player_in_id"] = player_in_id
    return await client.post(f"/api/matches/{match_id}/events", json=body, headers=cup.curator)


async def play(client, cup: Cup, match: dict, home_goals: int, away_goals: int, **penalties) -> dict:
    await start(client, cup, match)
    for team, goals in ((match["home_team"]["id"], home_goals), (match["away_team"]["id"], away_goals)):
        for _ in range(goals):
            assert (await event(client, cup, match["id"], "goal", cup.players[team][0])).status_code == 201
    response = await client.post(f"/api/matches/{match['id']}/finish", json=penalties, headers=cup.curator)
    assert response.status_code == 200, response.text
    return response.json()


async def test_lineup_rules(client, make_cup):
    cup = await make_cup()
    [match] = await matches_of(client, cup)
    home, away = cup.teams
    url = f"/api/matches/{match['id']}/lineups/{home}"

    foreign_rep = await client.put(
        url,
        json={"players": [{"player_id": cup.players[home][0], "shirt_number": 1, "is_starting": True}]},
        headers=cup.reps[away],
    )
    foreign_player = await client.put(
        url,
        json={"players": [{"player_id": cup.players[away][0], "shirt_number": 1, "is_starting": True}]},
        headers=cup.reps[home],
    )
    assert foreign_rep.status_code == 403
    assert foreign_player.status_code == 400 and foreign_player.json()["field"] == "players"

    assert (await submit_lineup(client, cup, match["id"], home)).status_code == 200
    lineup = (await client.get(url)).json()
    assert [(p["shirt_number"], p["is_starting"]) for p in lineup["players"]] == [
        (1, True),
        (2, True),
        (12, False),
    ]

    soon = (datetime.now(UTC) + timedelta(minutes=30)).isoformat()
    await client.patch(f"/api/matches/{match['id']}", json={"scheduled_at": soon}, headers=cup.organizer)
    locked = await submit_lineup(client, cup, match["id"], home)
    assert locked.status_code == 409 and locked.json()["code"] == "LINEUP_LOCKED"


async def test_curator_must_be_assigned(client, make_cup, make_user):
    cup = await make_cup()
    [match] = await matches_of(client, cup)
    other_curator, other = await make_user(UserRole.curator)
    rep, _ = await make_user()

    not_a_curator = await client.patch(
        f"/api/matches/{match['id']}", json={"curator_id": rep.id}, headers=cup.organizer
    )
    assert not_a_curator.status_code == 400 and not_a_curator.json()["field"] == "curator_id"
    assert (await client.post(f"/api/matches/{match['id']}/start", headers=other)).status_code == 403


async def test_substitutions(client, make_cup):
    cup = await make_cup()
    [match] = await matches_of(client, cup)
    home, away = cup.teams
    starter, partner, bench = cup.players[home]
    await start(client, cup, match)

    sub = await event(client, cup, match["id"], "substitution", starter, player_in_id=bench)
    assert sub.status_code == 201
    body = sub.json()["event"]
    assert (body["player"]["id"], body["player_in"]["id"], body["team"]["id"]) == (starter, bench, home)
    assert body["period"] == 1 and body["minute"] == 1

    # ушедший не может забить, а вышедший — может
    assert (await event(client, cup, match["id"], "goal", starter)).json()["code"] == "PLAYER_NOT_ON_FIELD"
    assert (await event(client, cup, match["id"], "goal", bench)).json()["home_score"] == 1

    on_field = await event(client, cup, match["id"], "substitution", partner, player_in_id=bench)
    assert on_field.status_code == 409 and on_field.json()["code"] == "PLAYER_ALREADY_ON_FIELD"
    off_field = await event(client, cup, match["id"], "substitution", starter, player_in_id=partner)
    assert off_field.json()["code"] == "PLAYER_NOT_ON_FIELD"
    other_team = await event(
        client, cup, match["id"], "substitution", partner, player_in_id=cup.players[away][2]
    )
    assert other_team.status_code == 400 and other_team.json()["field"] == "player_in_id"
    no_player_in = await event(client, cup, match["id"], "substitution", partner)
    assert no_player_in.status_code == 400 and no_player_in.json()["field"] == "player_in_id"

    # возвратная замена: ушедший игрок может выйти снова
    back = await event(client, cup, match["id"], "substitution", bench, player_in_id=starter)
    assert back.status_code == 201

    events = (await client.get(f"/api/matches/{match['id']}/events")).json()
    assert [e["type"] for e in events] == ["substitution", "goal", "substitution"]


async def test_sent_off_player_cannot_return(client, make_cup):
    cup = await make_cup()
    [match] = await matches_of(client, cup)
    starter, partner, bench = cup.players[cup.teams[0]]
    await start(client, cup, match)

    assert (await event(client, cup, match["id"], "red_card", starter)).status_code == 201

    back = await event(client, cup, match["id"], "substitution", partner, player_in_id=starter)
    replace_sent_off = await event(client, cup, match["id"], "substitution", starter, player_in_id=bench)
    assert back.status_code == 409 and back.json()["code"] == "PLAYER_SENT_OFF"
    assert replace_sent_off.json()["code"] == "PLAYER_SENT_OFF"


async def test_repeated_event_is_not_duplicated(client, make_cup):
    cup = await make_cup()
    [match] = await matches_of(client, cup)
    scorer = cup.players[cup.teams[0]][0]
    await start(client, cup, match)
    event_id = uuid.uuid4()

    first = await event(client, cup, match["id"], "goal", scorer, event_id=event_id)
    repeat = await event(client, cup, match["id"], "goal", scorer, event_id=event_id)

    assert (first.status_code, repeat.status_code) == (201, 200)
    assert repeat.json()["event"]["id"] == first.json()["event"]["id"]
    assert repeat.json()["home_score"] == 1
    assert len((await client.get(f"/api/matches/{match['id']}/events")).json()) == 1


async def test_cancel_event(client, make_cup):
    cup = await make_cup()
    [match] = await matches_of(client, cup)
    home, away = cup.teams
    starter, _, bench = cup.players[home]
    await start(client, cup, match)
    sub = (await event(client, cup, match["id"], "substitution", starter, player_in_id=bench)).json()
    goal = (await event(client, cup, match["id"], "goal", bench)).json()
    own_goal = (await event(client, cup, match["id"], "own_goal", cup.players[away][0])).json()
    assert (own_goal["home_score"], own_goal["away_score"]) == (2, 0)
    url = f"/api/matches/{match['id']}/events"

    # без замены вышедший игрок не мог бы забить — сначала нужно отменить гол
    dependent = await client.delete(f"{url}/{sub['event']['id']}", headers=cup.curator)
    assert dependent.status_code == 409 and dependent.json()["code"] == "EVENT_HAS_DEPENDENTS"

    score = await client.delete(f"{url}/{goal['event']['id']}", headers=cup.curator)
    assert score.json() == {"home_score": 1, "away_score": 0}
    assert (await client.delete(f"{url}/{sub['event']['id']}", headers=cup.curator)).status_code == 200
    assert [e["type"] for e in (await client.get(url)).json()] == ["own_goal"]


async def test_periods(client, make_cup):
    cup = await make_cup()
    [match] = await matches_of(client, cup)
    scorer = cup.players[cup.teams[0]][0]
    url = f"/api/matches/{match['id']}"
    await start(client, cup, match)

    assert (await client.post(f"{url}/end-period", headers=cup.curator)).json()["current_period"] is None
    in_break = await event(client, cup, match["id"], "goal", scorer)
    assert in_break.status_code == 409 and in_break.json()["code"] == "NO_ACTIVE_PERIOD"

    assert (await client.post(f"{url}/start-period", headers=cup.curator)).json()["current_period"] == 2
    second_half = (await event(client, cup, match["id"], "goal", scorer)).json()["event"]
    assert (second_half["period"], second_half["minute"]) == (2, 26)  # тайм по 25 минут

    await client.post(f"{url}/end-period", headers=cup.curator)
    extra = await client.post(f"{url}/start-period", headers=cup.curator)
    assert extra.status_code == 409 and extra.json()["code"] == "NO_MORE_PERIODS"


async def test_playoff_draw_needs_penalties_and_winner_advances(client, make_cup):
    cup = await make_cup(teams=4)
    semi1, semi2, final = await matches_of(client, cup)
    await start(client, cup, semi1)
    url = f"/api/matches/{semi1['id']}/finish"

    no_penalties = await client.post(url, headers=cup.curator)
    tied_penalties = await client.post(
        url, json={"home_penalties": 3, "away_penalties": 3}, headers=cup.curator
    )
    assert no_penalties.status_code == 409 and no_penalties.json()["code"] == "PENALTIES_REQUIRED"
    assert tied_penalties.status_code == 409

    finished = (
        await client.post(url, json={"home_penalties": 3, "away_penalties": 4}, headers=cup.curator)
    ).json()
    assert finished["status"] == "finished" and finished["result_type"] == "penalties"
    assert finished["winner_team_id"] == semi1["away_team"]["id"]

    await play(client, cup, semi2, 2, 1)
    final = (await client.get(f"/api/matches/{final['id']}")).json()
    assert (final["home_team"]["id"], final["away_team"]["id"]) == (
        semi1["away_team"]["id"],
        semi2["home_team"]["id"],
    )


async def test_penalties_only_in_playoff_draw(client, make_cup):
    cup = await make_cup()
    [match] = await matches_of(client, cup)
    await start(client, cup, match)
    await event(client, cup, match["id"], "goal", cup.players[cup.teams[0]][0])

    response = await client.post(
        f"/api/matches/{match['id']}/finish",
        json={"home_penalties": 5, "away_penalties": 4},
        headers=cup.curator,
    )

    assert response.status_code == 400 and response.json()["field"] == "home_penalties"


async def test_group_winners_go_to_playoff_and_tournament_finishes(client, make_cup):
    cup = await make_cup(teams=4, format="mixed", groups=2, advance=1)
    group_a, group_b, final = await matches_of(client, cup)
    assert final["stage"] == "playoff" and final["home_team"] is None

    await play(client, cup, group_a, 1, 0)
    assert (await client.get(f"/api/matches/{final['id']}")).json()[
        "home_team"
    ] is None  # группа B не доиграна
    await play(client, cup, group_b, 0, 2)

    final = (await client.get(f"/api/matches/{final['id']}")).json()
    assert (final["home_team"]["id"], final["away_team"]["id"]) == (
        group_a["home_team"]["id"],
        group_b["away_team"]["id"],
    )

    await play(client, cup, final, 1, 0)
    assert (await client.get(f"/api/tournaments/{cup.id}")).json()["status"] == "finished"
