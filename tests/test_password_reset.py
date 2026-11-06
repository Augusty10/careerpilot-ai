from datetime import datetime, timedelta, timezone
import pytest
from backend.database import get_users_collection
from backend.services.auth_service import hash_reset_token


@pytest.fixture
def reset_user(client):
    """Registers a user specifically for password reset tests."""
    payload = {
        "name": "Sam Reset",
        "email": "sam.reset@example.com",
        "password": "InitialPass123"
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    return payload


def test_forgot_password_generic_response(client, reset_user):
    """
    Verifies that POST /api/auth/forgot-password returns the identical generic
    message for both existing and non-existing email addresses.
    """
    # 1. Existing user
    res_existing = client.post("/api/auth/forgot-password", json={"email": reset_user["email"]})
    assert res_existing.status_code == 200
    msg_existing = res_existing.get_json().get("message")

    # 2. Non-existing user
    res_unknown = client.post("/api/auth/forgot-password", json={"email": "nobody@example.com"})
    assert res_unknown.status_code == 200
    msg_unknown = res_unknown.get_json().get("message")

    # Ensure responses are identical
    assert msg_existing == msg_unknown
    assert "reset link has been sent" in msg_existing.lower()


def test_password_reset_end_to_end(client, reset_user, monkeypatch):
    """
    Simulates complete password reset flow:
    Request reset -> capture raw token -> submit reset -> login with new password.
    """
    captured_links = []

    def fake_print(*args, **kwargs):
        text = " ".join(str(a) for a in args)
        captured_links.append(text)

    monkeypatch.setattr("sys.stdout.write", lambda s: captured_links.append(s))

    # Request reset
    forgot_res = client.post("/api/auth/forgot-password", json={"email": reset_user["email"]})
    assert forgot_res.status_code == 200

    # Retrieve stored token hash from database to find matching raw token or inject a known token
    users_col = get_users_collection()
    user_in_db = users_col.find_one({"email": reset_user["email"]})
    assert user_in_db is not None
    assert user_in_db.get("reset_token_hash") is not None
    assert user_in_db.get("reset_token_expiry") is not None

    # Let's test with a simulated known raw token
    known_raw_token = "my-secure-one-time-reset-token-xyz"
    known_hash = hash_reset_token(known_raw_token)
    now = datetime.now(timezone.utc)
    users_col.update_one(
        {"_id": user_in_db["_id"]},
        {"$set": {
            "reset_token_hash": known_hash,
            "reset_token_expiry": now + timedelta(minutes=15)
        }}
    )

    # Submit password reset with the valid token
    reset_res = client.post("/api/auth/reset-password", json={
        "token": known_raw_token,
        "new_password": "NewFresherPassword99"
    })
    assert reset_res.status_code == 200
    assert "successful" in reset_res.get_json().get("message", "").lower()

    # Verify old password cannot log in
    old_login = client.post("/api/auth/login", json={
        "email": reset_user["email"],
        "password": reset_user["password"]
    })
    assert old_login.status_code == 401

    # Verify new password can log in
    new_login = client.post("/api/auth/login", json={
        "email": reset_user["email"],
        "password": "NewFresherPassword99"
    })
    assert new_login.status_code == 200
    assert "token" in new_login.get_json()


def test_password_reset_reused_token_rejected(client, reset_user):
    """Verifies that a reset token cannot be used a second time."""
    known_raw_token = "token-for-single-use-testing"
    known_hash = hash_reset_token(known_raw_token)
    now = datetime.now(timezone.utc)

    users_col = get_users_collection()
    users_col.update_one(
        {"email": reset_user["email"]},
        {"$set": {
            "reset_token_hash": known_hash,
            "reset_token_expiry": now + timedelta(minutes=15)
        }}
    )

    # First use succeeds
    first_res = client.post("/api/auth/reset-password", json={
        "token": known_raw_token,
        "new_password": "FirstNewPassword1"
    })
    assert first_res.status_code == 200

    # Second attempt with the same token must fail
    second_res = client.post("/api/auth/reset-password", json={
        "token": known_raw_token,
        "new_password": "SecondNewPassword2"
    })
    assert second_res.status_code == 400
    assert "invalid or expired" in second_res.get_json().get("error", "").lower()


def test_password_reset_expired_token_rejected(client, reset_user):
    """Verifies that an expired reset token is rejected."""
    expired_token = "expired-token-12345"
    expired_hash = hash_reset_token(expired_token)
    # Set expiry in the past
    past_time = datetime.now(timezone.utc) - timedelta(minutes=10)

    users_col = get_users_collection()
    users_col.update_one(
        {"email": reset_user["email"]},
        {"$set": {
            "reset_token_hash": expired_hash,
            "reset_token_expiry": past_time
        }}
    )

    response = client.post("/api/auth/reset-password", json={
        "token": expired_token,
        "new_password": "NewPassword123"
    })
    assert response.status_code == 400
    assert "invalid or expired" in response.get_json().get("error", "").lower()


def test_password_reset_leak_check(client, reset_user):
    """Verifies reset tokens or password hashes never leak in reset responses."""
    raw_token = "leak-check-token-abc"
    now = datetime.now(timezone.utc)
    users_col = get_users_collection()
    users_col.update_one(
        {"email": reset_user["email"]},
        {"$set": {
            "reset_token_hash": hash_reset_token(raw_token),
            "reset_token_expiry": now + timedelta(minutes=15)
        }}
    )

    res = client.post("/api/auth/reset-password", json={
        "token": raw_token,
        "new_password": "NewCleanPassword1"
    })
    assert res.status_code == 200
    raw_body = res.data.decode("utf-8")
    assert "password_hash" not in raw_body
    assert "reset_token_hash" not in raw_body
    assert raw_token not in raw_body

