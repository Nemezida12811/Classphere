import pytest

BASE_URL = "/api/v1/locations/"


@pytest.fixture
def auth_headers(client):
    # Register a test user
    response = client.post("/api/v1/auth/register", json={
        "username": "locationuser",
        "email": "location@example.com",
        "password": "password123",
    })
    assert response.status_code == 201

    # Login and obtain JWT token
    response = client.post("/api/v1/auth/login-json", json={
        "username": "locationuser",
        "password": "password123",
    })
    assert response.status_code == 200

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def created_location(client, auth_headers):
    response = client.post(
        BASE_URL,
        json={
            "name": "Room 101",
            "building": "Main",
            "floor": 1,
            "description": "Computer laboratory",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


def test_get_empty_locations(client):
    response = client.get(BASE_URL)

    assert response.status_code == 200
    assert response.json() == []


def test_create_location_success(client, auth_headers):
    response = client.post(
        BASE_URL,
        json={
            "name": "Physics Lab",
            "building": "Building A",
            "floor": 2,
            "description": "Physics classroom",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Physics Lab"
    assert data["building"] == "Building A"
    assert data["floor"] == 2
    assert data["is_active"] is True
    assert "id" in data


def test_create_location_without_token(client):
    response = client.post(
        BASE_URL,
        json={"name": "Unauthorized Room"},
    )

    assert response.status_code == 401


def test_create_duplicate_location(client, auth_headers, created_location):
    response = client.post(
        BASE_URL,
        json={"name": created_location["name"]},
        headers=auth_headers,
    )

    assert response.status_code == 409


def test_get_location_by_id(client, created_location):
    location_id = created_location["id"]

    response = client.get(f"{BASE_URL}{location_id}")

    assert response.status_code == 200
    assert response.json()["id"] == location_id
    assert response.json()["name"] == "Room 101"


def test_get_nonexistent_location(client):
    response = client.get(f"{BASE_URL}99999")

    assert response.status_code == 404


def test_update_location(client, auth_headers, created_location):
    location_id = created_location["id"]

    response = client.put(
        f"{BASE_URL}{location_id}",
        json={
            "name": "Room 102",
            "floor": 3,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Room 102"
    assert response.json()["floor"] == 3
    assert response.json()["building"] == "Main"


def test_delete_location(client, auth_headers, created_location):
    location_id = created_location["id"]

    response = client.delete(
        f"{BASE_URL}{location_id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    # Deleted location should no longer exist
    response = client.get(f"{BASE_URL}{location_id}")
    assert response.status_code == 404


def test_update_without_token(client, created_location):
    location_id = created_location["id"]

    response = client.put(
        f"{BASE_URL}{location_id}",
        json={"name": "Unauthorized Update"},
    )

    assert response.status_code == 401


def test_invalid_pagination(client):
    response = client.get(
        BASE_URL,
        params={"skip": -1, "limit": 200},
    )

    assert response.status_code == 422