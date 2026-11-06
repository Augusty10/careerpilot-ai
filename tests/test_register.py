import json
import pytest


def test_register_success(client):
    """Verifies that a valid registration succeeds and returns HTTP 201 with user details."""
    payload = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "password": "Password123"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201

    data = response.get_json()
    assert "user" in data
    assert data["user"]["name"] == "Jane Doe"
    assert data["user"]["email"] == "jane.doe@example.com"
    assert "id" in data["user"]
    # Verify password_hash is never exposed
    assert "password_hash" not in data["user"]
    assert "password_hash" not in str(data)


def test_register_duplicate_email_rejected(client):
    """Verifies that duplicate email registrations are rejected with HTTP 409."""
    payload = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "password": "Password123"
    }
    # First registration succeeds
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with same email (even with different casing) must fail
    duplicate_payload = {
        "name": "Jane Duplicate",
        "email": "JANE.DOE@example.com",
        "password": "AnotherPassword456"
    }
    res2 = client.post("/api/auth/register", json=duplicate_payload)
    assert res2.status_code == 409
    data = res2.get_json()
    assert "error" in data
    assert "already exists" in data["error"].lower()


@pytest.mark.parametrize("weak_password, reason", [
    ("short1", "Password must be at least 8 characters long"),
    ("alllettersonly", "Password must contain at least one number"),
    ("1234567890", "Password must contain at least one letter"),
])
def test_register_weak_password_rejected(client, weak_password, reason):
    """Verifies that weak passwords lacking required length or complexity are rejected."""
    payload = {
        "name": "Weak Pass User",
        "email": "weak@example.com",
        "password": weak_password
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_register_invalid_email_rejected(client):
    """Verifies that malformed email addresses are rejected with HTTP 400."""
    payload = {
        "name": "Invalid Email",
        "email": "not-an-email",
        "password": "Password123"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_register_password_hash_never_returned(client):
    """Ensures password_hash never appears anywhere in the register response body."""
    payload = {
        "name": "Secret User",
        "email": "secret@example.com",
        "password": "SecretPassword99"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    raw_response = response.data.decode("utf-8")
    assert "password_hash" not in raw_response
    assert "reset_token_hash" not in raw_response

