from app.models.enums import UserRole


async def test_list_users_forbidden_for_team_rep(client, make_user):
    _, headers = await make_user(UserRole.team_rep)

    response = await client.get("/api/users", headers=headers)

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


async def test_organizer_lists_curators(client, make_user):
    _, headers = await make_user(UserRole.organizer)
    curator, _ = await make_user(UserRole.curator)
    await make_user(UserRole.team_rep)

    response = await client.get("/api/users", params={"role": "curator"}, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == curator.id


async def test_admin_changes_role(client, make_user):
    _, headers = await make_user(UserRole.admin)
    user, _ = await make_user(UserRole.team_rep)

    response = await client.patch(f"/api/users/{user.id}/role", json={"role": "curator"}, headers=headers)

    assert response.status_code == 200
    assert response.json()["role"] == "curator"


async def test_role_change_takes_effect_without_new_token(client, make_user):
    _, admin_headers = await make_user(UserRole.admin)
    user, user_headers = await make_user(UserRole.team_rep)

    await client.patch(f"/api/users/{user.id}/role", json={"role": "organizer"}, headers=admin_headers)
    response = await client.get("/api/users", headers=user_headers)

    assert response.status_code == 200


async def test_only_admin_changes_roles(client, make_user):
    _, headers = await make_user(UserRole.organizer)
    user, _ = await make_user(UserRole.team_rep)

    response = await client.patch(f"/api/users/{user.id}/role", json={"role": "admin"}, headers=headers)

    assert response.status_code == 403


async def test_admin_cannot_demote_self(client, make_user):
    admin, headers = await make_user(UserRole.admin)

    response = await client.patch(f"/api/users/{admin.id}/role", json={"role": "team_rep"}, headers=headers)

    assert response.status_code == 409
    assert response.json()["code"] == "CANNOT_CHANGE_OWN_ROLE"


async def test_change_role_of_unknown_user_returns_404(client, make_user):
    _, headers = await make_user(UserRole.admin)

    response = await client.patch("/api/users/999/role", json={"role": "curator"}, headers=headers)

    assert response.status_code == 404
