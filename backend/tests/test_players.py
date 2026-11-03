from app.models.enums import UserRole
from tests.conftest import JPEG, PNG, player_form


async def post_player(client, headers, photo=("p.png", PNG, "image/png"), **form):
    files = {"photo": photo} if photo else None
    return await client.post("/api/players", data=player_form(**form), files=files, headers=headers)


async def test_create_player_saves_photo(client, make_user, media_dir):
    _, headers = await make_user()

    response = await post_player(client, headers, middle_name="Сергеевич")

    assert response.status_code == 201
    body = response.json()
    assert body["last_name"] == "Иванов" and body["middle_name"] == "Сергеевич"
    assert body["birth_date"] == "2003-05-14"
    assert body["photo_url"].startswith("/media/players/") and body["photo_url"].endswith(".png")
    assert (media_dir / body["photo_url"].removeprefix("/media/")).read_bytes() == PNG


async def test_photo_is_required(client, make_user):
    _, headers = await make_user()

    response = await post_player(client, headers, photo=None)

    assert response.status_code == 400
    assert response.json()["field"] == "photo"


async def test_photo_must_be_an_image(client, make_user, media_dir):
    _, headers = await make_user()

    response = await post_player(client, headers, photo=("p.png", b"not an image", "image/png"))

    assert response.status_code == 400
    assert response.json()["field"] == "photo"
    assert not any(media_dir.rglob("*.*"))


async def test_required_fields(client, make_user):
    _, headers = await make_user()

    no_name = await post_player(client, headers, last_name=None)
    no_birth_date = await post_player(client, headers, birth_date=None)

    assert (no_name.status_code, no_name.json()["field"]) == (400, "last_name")
    assert (no_birth_date.status_code, no_birth_date.json()["field"]) == (400, "birth_date")


async def test_birth_date_cannot_be_in_future(client, make_user):
    _, headers = await make_user()

    response = await post_player(client, headers, birth_date="2999-01-01")

    assert response.status_code == 400
    assert response.json()["field"] == "birth_date"


async def test_personal_data_consent_required(client, make_user, media_dir):
    _, headers = await make_user()

    response = await post_player(client, headers, pd_consent="false")

    assert response.status_code == 400
    assert response.json()["field"] == "pd_consent"
    assert not any(media_dir.rglob("*.*"))


async def test_create_player_straight_into_team(client, make_user, make_team):
    _, owner = await make_user()
    _, other = await make_user()
    team = await make_team(owner)

    created = await post_player(client, owner, team_id=str(team["id"]))
    foreign = await post_player(client, other, team_id=str(team["id"]))

    assert created.status_code == 201
    assert [e["player"]["id"] for e in (await client.get(f"/api/teams/{team['id']}/players")).json()] == [
        created.json()["id"]
    ]
    assert foreign.status_code == 403


async def test_only_team_rep_creates_players(client, make_user):
    _, headers = await make_user(UserRole.organizer)

    assert (await post_player(client, headers)).status_code == 403


async def test_search_players_by_name(client, make_user, make_player):
    _, rep = await make_user()
    _, organizer = await make_user(UserRole.organizer)
    await make_player(rep, last_name="Иванов", first_name="Пётр")
    await make_player(rep, last_name="Иванов", first_name="Сергей")
    await make_player(rep, last_name="Петров", first_name="Иван")

    response = await client.get("/api/players", params={"search": "иванов пётр"}, headers=organizer)

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["birth_date"] == "2003-05-14"


async def test_search_players_requires_role(client, make_user):
    _, curator = await make_user(UserRole.curator)

    assert (await client.get("/api/players")).status_code == 401
    assert (await client.get("/api/players", headers=curator)).status_code == 403


async def test_public_profile_hides_birth_date(client, make_user, make_team, make_player):
    _, owner = await make_user()
    team = await make_team(owner)
    player = await make_player(owner, team_id=str(team["id"]))

    response = await client.get(f"/api/players/{player['id']}")

    assert response.status_code == 200
    body = response.json()
    assert "birth_date" not in body
    assert [t["id"] for t in body["teams"]] == [team["id"]]
    assert body["totals"] == {"matches": 0, "goals": 0, "yellow_cards": 0, "red_cards": 0}


async def test_update_player_permissions(client, make_user, make_team, make_player):
    _, creator = await make_user()
    _, team_owner = await make_user()
    _, stranger = await make_user()
    player = await make_player(creator)
    team = await make_team(team_owner)
    await client.post(
        f"/api/teams/{team['id']}/players", json={"player_id": player["id"]}, headers=team_owner
    )
    url = f"/api/players/{player['id']}"

    assert (await client.patch(url, json={"first_name": "Павел"}, headers=stranger)).status_code == 403
    by_creator = await client.patch(url, json={"first_name": "Павел"}, headers=creator)
    by_team_owner = await client.patch(url, json={"middle_name": "Ильич"}, headers=team_owner)

    assert by_creator.status_code == 200
    assert by_team_owner.json()["first_name"] == "Павел"
    assert by_team_owner.json()["middle_name"] == "Ильич"


async def test_replace_photo_deletes_old_file(client, make_user, make_player, media_dir):
    _, headers = await make_user()
    player = await make_player(headers)
    old_file = media_dir / player["photo_url"].removeprefix("/media/")

    response = await client.put(
        f"/api/players/{player['id']}/photo", files={"photo": ("p.jpg", JPEG, "image/jpeg")}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["photo_url"].endswith(".jpg")
    assert not old_file.exists()
    assert (media_dir / response.json()["photo_url"].removeprefix("/media/")).exists()


async def test_unknown_player_returns_404(client):
    assert (await client.get("/api/players/999")).status_code == 404
