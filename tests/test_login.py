import pytest


@pytest.fixture
def registered_user(client):
    """Registers a default test user."""
    payload = {
        "name": "Alex Candidate",
        "email": "alex@careerpilot.ai",
        "password": "FresherPassword1"
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    return payload


def test_login_success(client, registered_user):
    """Verifies that valid credentials return HTTP 200 with JWT and user info."""
    login_data = {
        "email": registered_user["email"],
        "password": registered_user["password"]
    }
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200

    data = response.get_json()
    assert "token" in data
    assert isinstance(data["token"], str)
    assert len(data["token"]) > 20
    assert "user" in data
    assert data["user"]["email"] == "alex@careerpilot.ai"
    assert data["user"]["name"] == "Alex Candidate"
    # Ensure password_hash is not present
    assert "password_hash" not in data["user"]
    assert "password_hash" not in str(data)


def test_login_wrong_password_rejected(client, registered_user):
    """Verifies that an incorrect password produces a generic 401 error."""
    login_data = {
        "email": registered_user["email"],
        "password": "WrongPassword999"
    }
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 401
    data = response.get_json()
    assert data.get("error") == "Invalid email or password"


def test_login_unknown_email_same_generic_error(client, registered_user):
    """
    Verifies that an unknown email returns the exact same generic error message
    and 401 status code as a wrong password to prevent user enumeration.
    """
    # 1. Attempt login with non-existent user
    unknown_data = {
        "email": "nonexistent@careerpilot.ai",
        "password": "FresherPassword1"
    }
    unknown_res = client.post("/api/auth/login", json=unknown_data)
    assert unknown_res.status_code == 401

    # 2. Attempt login with existing user but wrong password
    wrong_pass_data = {
        "email": registered_user["email"],
        "password": "WrongPassword999"
    }
    wrong_pass_res = client.post("/api/auth/login", json=wrong_pass_data)
    assert wrong_pass_res.status_code == 401

    # Both responses must be identical
    assert unknown_res.get_json() == wrong_pass_res.get_json()
    assert unknown_res.get_json().get("error") == "Invalid email or password"


def test_login_password_hash_never_returned(client, registered_user):
    """Verifies that password_hash never appears in login response payload."""
    login_data = {
        "email": registered_user["email"],
        "password": registered_user["password"]
    }
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    raw_response = response.data.decode("utf-8")
    assert "password_hash" not in raw_response
    assert "reset_token_hash" not in raw_response

