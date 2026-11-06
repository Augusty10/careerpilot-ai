import shutil
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, request, jsonify, g
from pydantic import ValidationError

from backend.config import Config
from backend.database import get_profiles_collection
from backend.models.profile import (
    CandidateProfileSchema,
    get_empty_profile_skeleton,
    serialize_profile,
)
from backend.services.auth_service import token_required
from backend.services.resume_service import process_resume_upload, ResumeParsingError
from backend.services.ai_service import get_ai_service, AIExtractionError

profiles_bp = Blueprint("profiles", __name__, url_prefix="/api/profile")


@profiles_bp.route("", methods=["GET"])
@token_required
def get_my_profile(current_user):
    """
    Returns the current user's master career profile.
    If no profile has been saved yet, returns an empty skeleton initialized
    with the user's registered name and email.
    """
    user_id = str(current_user["_id"])
    col = get_profiles_collection()
    profile = col.find_one({"user_id": user_id})

    if not profile:
        skeleton = get_empty_profile_skeleton(
            user_id=user_id,
            full_name=current_user.get("name", ""),
            email=current_user.get("email", ""),
        )
        return jsonify({"profile": skeleton}), 200

    return jsonify({"profile": serialize_profile(profile)}), 200


@profiles_bp.route("", methods=["PUT"])
@token_required
def save_or_update_profile(current_user):
    """
    Creates or updates the current user's profile.
    Validates input using Pydantic schema and calculates completeness.
    Guarantees strict tenant isolation by always scoping to current_user['_id'].
    """
    data = request.get_json(silent=True) or {}
    user_id = str(current_user["_id"])

    try:
        validated = CandidateProfileSchema(**data)
    except ValidationError as err:
        errors = [f"{e['loc'][0]}: {e['msg']}" for e in err.errors()]
        return jsonify({"error": "; ".join(errors)}), 400

    col = get_profiles_collection()
    now = datetime.now(timezone.utc)

    profile_dict = validated.model_dump()
    profile_dict["user_id"] = user_id
    profile_dict["updated_at"] = now

    existing = col.find_one({"user_id": user_id})
    if existing:
        # Preserve original creation date
        profile_dict["created_at"] = existing.get("created_at", now)
        col.replace_one({"user_id": user_id}, profile_dict)
    else:
        profile_dict["created_at"] = now
        col.insert_one(profile_dict)

    saved_doc = col.find_one({"user_id": user_id})
    return jsonify({
        "message": "Profile saved successfully",
        "profile": serialize_profile(saved_doc)
    }), 200


@profiles_bp.route("/upload", methods=["POST"])
@token_required
def upload_resume_and_extract(current_user):
    """
    Uploads a PDF/DOCX resume file, verifies magic bytes, extracts text,
    runs AI extraction, and returns structured profile data.
    CRITICAL: Does NOT save to database; candidate must review first.
    """
    user_id = str(current_user["_id"])

    # Look for file in request
    uploaded_file = request.files.get("resume") or request.files.get("file")
    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"error": "No resume file was uploaded. Please provide a .pdf or .docx file."}), 400

    file_bytes = uploaded_file.read()
    if not file_bytes:
        return jsonify({"error": "The uploaded file is empty."}), 400

    # 1. Validate, save to private storage, and extract plain text
    try:
        extracted_text, saved_path = process_resume_upload(
            user_id=user_id,
            filename=uploaded_file.filename,
            file_bytes=file_bytes,
            content_type=uploaded_file.content_type or "",
        )
    except ResumeParsingError as rpe:
        return jsonify({"error": str(rpe)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to process resume document: {str(e)}"}), 400

    # 2. Run AI extraction
    try:
        ai_service = get_ai_service()
        extracted_data = ai_service.extract_profile_data(extracted_text)
    except AIExtractionError as aie:
        return jsonify({"error": str(aie)}), 502
    except Exception as e:
        return jsonify({"error": f"AI extraction error: {str(e)}"}), 502

    return jsonify({
        "message": "Resume parsed and structured successfully. Please review and verify the data before saving.",
        "extracted_data": extracted_data
    }), 200


@profiles_bp.route("/approve", methods=["POST"])
@token_required
def approve_profile(current_user):
    """
    Marks the current user's profile as 'approved' after candidate review.
    """
    user_id = str(current_user["_id"])
    col = get_profiles_collection()
    profile = col.find_one({"user_id": user_id})

    if not profile:
        return jsonify({"error": "No profile found to approve. Please create or save your profile first."}), 404

    now = datetime.now(timezone.utc)
    col.update_one(
        {"user_id": user_id},
        {"$set": {"profile_status": "approved", "updated_at": now}}
    )

    updated_doc = col.find_one({"user_id": user_id})
    return jsonify({
        "message": "Master profile approved successfully! It is now the official source of truth.",
        "profile": serialize_profile(updated_doc)
    }), 200


@profiles_bp.route("", methods=["DELETE"])
@token_required
def delete_profile(current_user):
    """
    Deletes the current user's profile and cleans up private stored resume files.
    User-controlled privacy deletion.
    """
    user_id = str(current_user["_id"])
    col = get_profiles_collection()

    delete_result = col.delete_one({"user_id": user_id})

    # Clean up user's private storage folder
    user_storage_dir = Path(Config.PRIVATE_STORAGE_DIR) / user_id
    if user_storage_dir.exists():
        try:
            shutil.rmtree(user_storage_dir, ignore_errors=True)
        except Exception:
            pass

    return jsonify({
        "message": "Profile and associated private resume files deleted successfully.",
        "deleted": bool(delete_result.deleted_count > 0)
    }), 200

