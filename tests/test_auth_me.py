import pytest


@pytest.fixture
def auth_session(client):
    """Registers and logs in a test user, returning auth token and user dict."""
    user_data = {
        "name": "Jordan Lee",
        "email": "jordan.lee@example.com",
        "password": "InitialPass123"
    }
    client.post("/api/auth/register", json=user_data)
    login_res = client.post("/api/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    token = login_res.get_json()["token"]
    return {
        "token": token,
        "email": user_data["email"],
        "password": user_data["password"],
        "name": user_data["name"]
    }


def test_me_without_token_returns_401(client):
    """Verifies that accessing /api/auth/me without an Authorization header returns 401."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data


def test_me_with_invalid_token_returns_401(client):
    """Verifies that a tampered or invalid Bearer token returns 401."""
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401


def test_me_with_valid_token_returns_user(client, auth_session):
    """Verifies that a valid token returns the user profile."""
    headers = {"Authorization": f"Bearer {auth_session['token']}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200

    data = response.get_json()
    assert "user" in data
    assert data["user"]["email"] == auth_session["email"]
    assert data["user"]["name"] == auth_session["name"]
    assert "id" in data["user"]
    # Verify password_hash is never returned
    assert "password_hash" not in data["user"]
    assert "password_hash" not in str(data)


def test_put_me_update_name(client, auth_session):
    """Verifies updating the display name via PUT /api/auth/me."""
    headers = {"Authorization": f"Bearer {auth_session['token']}"}
    update_payload = {"name": "Jordan Updated"}
    response = client.put("/api/auth/me", headers=headers, json=update_payload)
    assert response.status_code == 200

    data = response.get_json()
    assert data["user"]["name"] == "Jordan Updated"

    # Verify subsequent GET reflects the change
    get_res = client.get("/api/auth/me", headers=headers)
    assert get_res.get_json()["user"]["name"] == "Jordan Updated"


def test_put_me_change_password(client, auth_session):
    """Verifies updating user password with current password verification."""
    headers = {"Authorization": f"Bearer {auth_session['token']}"}

    # 1. Attempt with wrong current password -> rejected
    wrong_pass_payload = {
        "current_password": "WrongCurrentPass99",
        "new_password": "BrandNewPass456"
    }
    fail_res = client.put("/api/auth/me", headers=headers, json=wrong_pass_payload)
    assert fail_res.status_code == 400

    # 2. Attempt with correct current password -> success
    valid_payload = {
        "current_password": auth_session["password"],
        "new_password": "BrandNewPass456"
    }
    success_res = client.put("/api/auth/me", headers=headers, json=valid_payload)
    assert success_res.status_code == 200

    # 3. Old password must no longer work for login
    old_login = client.post("/api/auth/login", json={
        "email": auth_session["email"],
        "password": auth_session["password"]
    })
    assert old_login.status_code == 401

    # 4. New password works for login
    new_login = client.post("/api/auth/login", json={
        "email": auth_session["email"],
        "password": "BrandNewPass456"
    })
    assert new_login.status_code == 200

