def test_register_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "role": "student",
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["is_active"] is True
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_username(client):
    user = {
        "username": "testuser",
        "email": "first@example.com",
        "password": "password123",
    }

    first_response = client.post(
        "/api/v1/auth/register",
        json=user,
    )
    assert first_response.status_code == 201

    user["email"] = "second@example.com"

    response = client.post(
        "/api/v1/auth/register",
        json=user,
    )

    assert response.status_code == 409


def test_register_invalid_email(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123",
        },
    )

    assert response.status_code == 422


def test_register_short_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "123",
        },
    )

    assert response.status_code == 422


def test_login_json_success(client):
    client.post("/api/v1/auth/register", json={
        "username": "loginuser",
        "email": "login@example.com",
        "password": "password123"
    })

    response = client.post("/api/v1/auth/login-json", json={
        "username": "loginuser",
        "password": "password123"
    })

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json={
        "username": "loginuser",
        "email": "login@example.com",
        "password": "password123"
    })

    response = client.post("/api/v1/auth/login-json", json={
        "username": "loginuser",
        "password": "wrongpassword"
    })

    assert response.status_code == 401


def test_login_form_success(client):
    client.post("/api/v1/auth/register", json={
        "username": "formuser",
        "email": "form@example.com",
        "password": "password123"
    })

    response = client.post("/api/v1/auth/login", data={
        "username": "formuser",
        "password": "password123"
    })

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_get_profile_with_token(client):
    client.post("/api/v1/auth/register", json={
        "username": "profileuser",
        "email": "profile@example.com",
        "password": "password123"
    })

    login = client.post("/api/v1/auth/login-json", json={
        "username": "profileuser",
        "password": "password123"
    })

    assert login.status_code == 200
    token = login.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["username"] == "profileuser"


def test_get_profile_without_token(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401