async def register(client, email="rep@example.com", password="password123", full_name="Сергеев Андрей"):
    return await client.post(
        "/api/auth/register", json={"email": email, "password": password, "full_name": full_name}
    )


async def test_register_creates_team_rep(client):
    response = await register(client, email="Rep@Example.com")

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "rep@example.com"
    assert body["role"] == "team_rep"
    assert "password" not in body and "password_hash" not in body


async def test_register_duplicate_email_returns_409(client):
    await register(client)

    response = await register(client, email="REP@example.com")

    assert response.status_code == 409
    assert response.json() == {
        "code": "EMAIL_TAKEN",
        "message": "Пользователь с таким email уже существует",
        "field": "email",
    }


async def test_register_short_password_returns_400(client):
    response = await register(client, password="123")

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert response.json()["field"] == "password"


async def test_login_returns_token_that_works_for_me(client):
    await register(client)

    login = await client.post("/api/auth/login", json={"email": "rep@example.com", "password": "password123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "rep@example.com"


async def test_login_wrong_password_returns_401(client):
    await register(client)

    response = await client.post(
        "/api/auth/login", json={"email": "rep@example.com", "password": "wrong-pass"}
    )

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


async def test_me_without_token_returns_401(client):
    response = await client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


async def test_me_with_invalid_token_returns_401(client):
    response = await client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-token"})

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_TOKEN"
