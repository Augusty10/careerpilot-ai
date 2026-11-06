import hashlib
import inspect
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Tuple, Dict, Any, Optional

import bcrypt
import jwt
from bson import ObjectId
from flask import request, jsonify, g

from backend.config import Config
from backend.database import get_users_collection


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt with auto-generated salt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def check_password(password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def generate_access_token(user_id: str, email: str) -> str:
    """Generates a signed JWT access token with an expiration time."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=Config.JWT_EXPIRY_MINUTES)
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT access token."""
    return jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])


def generate_reset_token(expiry_minutes: int = 15) -> Tuple[str, str, datetime]:
    """
    Generates a secure random reset token.
    Returns:
        (raw_token, hashed_token, expiry_datetime)
    Only hashed_token is stored in the database.
    """
    raw_token = secrets.token_urlsafe(32)
    hashed_token = hash_reset_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
    return raw_token, hashed_token, expires_at


def hash_reset_token(raw_token: str) -> str:
    """Returns SHA-256 hex digest of a raw token."""
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


def token_required(f):
    """
    Reusable decorator for protecting endpoints with JWT authentication.
    Verifies Bearer token, fetches user from database, attaches user to g.current_user,
    and injects 'current_user' if present in the handler's signature.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authorization token is missing"}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({
                "error": "Invalid Authorization header format. Expected 'Bearer <token>'"
            }), 401

        token = parts[1]

        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if not user_id:
                return jsonify({"error": "Invalid token payload"}), 401

            # Query database for user document
            users_col = get_users_collection()
            try:
                obj_id = ObjectId(user_id)
            except Exception:
                return jsonify({"error": "Invalid user identifier"}), 401

            user = users_col.find_one({"_id": obj_id})
            if not user:
                return jsonify({"error": "User not found"}), 401

            # Attach user to Flask request context
            g.current_user = user

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired. Please log in again."}), 401
        except (jwt.InvalidTokenError, Exception):
            return jsonify({"error": "Invalid or malformed token"}), 401

        # Support both g.current_user and current_user keyword argument
        sig = inspect.signature(f)
        if "current_user" in sig.parameters:
            return f(*args, current_user=user, **kwargs)
        return f(*args, **kwargs)

    return decorated

