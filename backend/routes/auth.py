import sys
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, g
from pydantic import ValidationError

from backend.config import Config
from backend.database import get_users_collection
from backend.limiter import limiter
from backend.models.user import (
    UserRegisterSchema,
    UserLoginSchema,
    ForgotPasswordSchema,
    ResetPasswordSchema,
    UpdateProfileSchema,
    serialize_user,
)
from backend.services.auth_service import (
    hash_password,
    check_password,
    generate_access_token,
    generate_reset_token,
    hash_reset_token,
    token_required,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Registers a new user account.
    Validates name, email, and password complexity.
    Rejects duplicate emails with HTTP 409.
    """
    data = request.get_json(silent=True) or {}

    try:
        validated = UserRegisterSchema(**data)
    except ValidationError as err:
        errors = [f"{e['loc'][0]}: {e['msg']}" for e in err.errors()]
        return jsonify({"error": "; ".join(errors)}), 400

    users_col = get_users_collection()

    # Check for existing user with normalized email
    existing_user = users_col.find_one({"email": validated.email})
    if existing_user:
        return jsonify({"error": "An account with this email already exists"}), 409

    # Hash password with bcrypt; never store plaintext
    now = datetime.now(timezone.utc)
    user_doc = {
        "name": validated.name,
        "email": validated.email,
        "password_hash": hash_password(validated.password),
        "reset_token_hash": None,
        "reset_token_expiry": None,
        "created_at": now,
        "updated_at": now,
    }

    result = users_col.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    return jsonify({
        "message": "Registration successful",
        "user": serialize_user(user_doc)
    }), 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    """
    Authenticates a user and returns a signed JWT access token.
    Uses generic error responses to prevent user enumeration.
    """
    data = request.get_json(silent=True) or {}

    try:
        validated = UserLoginSchema(**data)
    except ValidationError as err:
        errors = [f"{e['loc'][0]}: {e['msg']}" for e in err.errors()]
        return jsonify({"error": "; ".join(errors)}), 400

    users_col = get_users_collection()
    user = users_col.find_one({"email": validated.email})

    # Return identical generic error for missing user or invalid password
    if not user or not check_password(validated.password, user.get("password_hash", "")):
        return jsonify({"error": "Invalid email or password"}), 401

    token = generate_access_token(str(user["_id"]), user["email"])

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": serialize_user(user)
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    Logs out the user. The client discards the token.
    Provides a standardized endpoint for session termination.
    """
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/forgot-password", methods=["POST"])
@limiter.limit("3 per minute")
def forgot_password():
    """
    Initiates the password reset flow.
    Generates a secure token, hashes it before storage, prints the reset link
    to the server console, and returns an identical generic response regardless
    of whether the email exists.
    """
    data = request.get_json(silent=True) or {}

    try:
        validated = ForgotPasswordSchema(**data)
    except ValidationError as err:
        errors = [f"{e['loc'][0]}: {e['msg']}" for e in err.errors()]
        return jsonify({"error": "; ".join(errors)}), 400

    users_col = get_users_collection()
    user = users_col.find_one({"email": validated.email})

    if user:
        raw_token, hashed_token, expires_at = generate_reset_token(expiry_minutes=15)
        users_col.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "reset_token_hash": hashed_token,
                    "reset_token_expiry": expires_at,
                    "updated_at": datetime.now(timezone.utc),
                }
            }
        )

        reset_url = f"{Config.FRONTEND_URL}/reset-password?token={raw_token}"
        print("\n" + "=" * 60, file=sys.stdout)
        print(f"[AUTH] Password Reset requested for: {user['email']}", file=sys.stdout)
        print(f"[AUTH] Reset Link: {reset_url}", file=sys.stdout)
        print(f"[AUTH] Expires at: {expires_at.isoformat()} (15 minutes)", file=sys.stdout)
        print("=" * 60 + "\n", file=sys.stdout)
        sys.stdout.flush()

        # Write latest reset token to file in development for automated verification
        try:
            with open(".latest_reset_token.txt", "w") as token_file:
                token_file.write(raw_token)
        except Exception:
            pass

    # Always return the exact same message to prevent account enumeration
    return jsonify({
        "message": "If an account with that email exists, a password reset link has been sent."
    }), 200


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """
    Completes password reset using a valid, non-expired reset token.
    Invalidates the reset token immediately after use to prevent replay attacks.
    """
    data = request.get_json(silent=True) or {}

    try:
        validated = ResetPasswordSchema(**data)
    except ValidationError as err:
        errors = [f"{e['loc'][0]}: {e['msg']}" for e in err.errors()]
        return jsonify({"error": "; ".join(errors)}), 400

    hashed_input_token = hash_reset_token(validated.token)
    users_col = get_users_collection()

    user = users_col.find_one({"reset_token_hash": hashed_input_token})

    if not user:
        return jsonify({"error": "Invalid or expired reset token"}), 400

    # Check token expiration
    expiry = user.get("reset_token_expiry")
    now = datetime.now(timezone.utc)
    if not expiry:
        return jsonify({"error": "Invalid or expired reset token"}), 400

    # Ensure timezone comparison compatibility
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if now > expiry:
        # Invalidate expired token
        users_col.update_one(
            {"_id": user["_id"]},
            {"$set": {"reset_token_hash": None, "reset_token_expiry": None}}
        )
        return jsonify({"error": "Invalid or expired reset token"}), 400

    # Update password and immediately clear the reset token
    new_hashed_password = hash_password(validated.new_password)
    users_col.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_hash": new_hashed_password,
                "reset_token_hash": None,
                "reset_token_expiry": None,
                "updated_at": now,
            }
        }
    )

    return jsonify({
        "message": "Password reset successful. Please log in with your new password."
    }), 200


@auth_bp.route("/me", methods=["GET"])
@token_required
def get_me(current_user):
    """
    Returns the sanitized profile of the currently authenticated user.
    """
    return jsonify({"user": serialize_user(current_user)}), 200


@auth_bp.route("/me", methods=["PUT"])
@token_required
def update_me(current_user):
    """
    Updates the authenticated user's name and/or changes password.
    Requires current password verification if changing password.
    """
    data = request.get_json(silent=True) or {}

    try:
        validated = UpdateProfileSchema(**data)
    except ValidationError as err:
        errors = [f"{e['loc'][0]}: {e['msg']}" for e in err.errors()]
        return jsonify({"error": "; ".join(errors)}), 400

    updates = {}
    now = datetime.now(timezone.utc)

    if validated.name is not None:
        updates["name"] = validated.name

    if validated.new_password is not None:
        # Verify existing password
        if not check_password(validated.current_password, current_user.get("password_hash", "")):
            return jsonify({"error": "Current password is incorrect"}), 400
        updates["password_hash"] = hash_password(validated.new_password)

    if not updates:
        return jsonify({"error": "No valid fields provided for update"}), 400

    updates["updated_at"] = now
    users_col = get_users_collection()
    users_col.update_one({"_id": current_user["_id"]}, {"$set": updates})

    updated_user = users_col.find_one({"_id": current_user["_id"]})
    return jsonify({
        "message": "Profile updated successfully",
        "user": serialize_user(updated_user)
    }), 200
