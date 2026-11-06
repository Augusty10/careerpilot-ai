"""
Resume Generation and Management Routes.
Protected endpoints for generating, updating, duplicating, listing,
and exporting ATS resumes.
"""

from flask import Blueprint, request, jsonify, send_file
from bson import ObjectId
from pydantic import ValidationError

from backend.services.auth_service import token_required
from backend.database import get_resumes_collection, get_profiles_collection
from backend.models.resume import (
    ResumeGenerateRequestSchema,
    ResumeGenerateMultipleRequestSchema,
    ResumeUpdateRequestSchema,
    serialize_resume
)
from backend.services.resume_generation_service import (
    generate_single_resume,
    generate_multiple_resumes,
    update_resume,
    duplicate_resume,
    delete_resume,
    get_resume_export_path,
    DEFAULT_FRESHER_ROLES
)


resumes_bp = Blueprint("resumes", __name__, url_prefix="/api/resumes")


@resumes_bp.route("/roles", methods=["GET"])
@token_required
def get_predefined_roles(current_user):
    """Returns a list of recommended fresher target roles for quick selection."""
    return jsonify({
        "status": "success",
        "roles": DEFAULT_FRESHER_ROLES
    }), 200


@resumes_bp.route("/generate", methods=["POST"])
@token_required
def generate_resume(current_user):
    """
    Generates a role-tailored resume from the candidate's approved master profile.
    Auto-increments version and exports ATS PDF and DOCX.
    """
    data = request.get_json() or {}
    try:
        req = ResumeGenerateRequestSchema(**data)
    except ValidationError as e:
        return jsonify({
            "status": "error",
            "message": "Validation failed",
            "errors": e.errors()
        }), 400

    try:
        resume, warnings = generate_single_resume(
            user_id=current_user["_id"],
            target_role=req.target_role,
            template=req.template or "modern",
            resume_name=req.resume_name
        )
        return jsonify({
            "status": "success",
            "message": f"Resume for '{req.target_role}' successfully generated.",
            "resume": resume,
            "warnings": warnings
        }), 201
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to generate resume: {str(e)}"
        }), 500


@resumes_bp.route("/generate-multiple", methods=["POST"])
@token_required
def generate_multiple_roles(current_user):
    """
    Generates multiple role-specific resumes in a single batch (max 5).
    """
    data = request.get_json() or {}
    try:
        req = ResumeGenerateMultipleRequestSchema(**data)
    except ValidationError as e:
        return jsonify({
            "status": "error",
            "message": "Validation failed",
            "errors": e.errors()
        }), 400

    try:
        resumes, warnings = generate_multiple_resumes(
            user_id=current_user["_id"],
            target_roles=req.target_roles,
            template=req.template or "modern"
        )
        return jsonify({
            "status": "success",
            "message": f"Successfully generated {len(resumes)} resumes.",
            "resumes": resumes,
            "warnings": warnings
        }), 201
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Batch generation failed: {str(e)}"
        }), 500


@resumes_bp.route("", methods=["GET"])
@token_required
def list_resumes(current_user):
    """
    Lists all resumes belonging to the authenticated user.
    Includes is_outdated calculation by comparing with the current master profile.
    """
    resumes_col = get_resumes_collection()
    profiles_col = get_profiles_collection()

    master_profile = profiles_col.find_one({"user_id": str(current_user["_id"])})
    master_updated_at = master_profile.get("updated_at") if master_profile else None

    # Fetch user resumes sorted by target_role and descending version
    cursor = resumes_col.find({"user_id": str(current_user["_id"])}).sort([
        ("target_role", 1),
        ("version", -1)
    ])

    resumes = [serialize_resume(doc, master_updated_at) for doc in cursor]

    # Group by role for convenience
    grouped: dict = {}
    for r in resumes:
        role = r.get("target_role", "Other")
        if role not in grouped:
            grouped[role] = []
        grouped[role].append(r)

    return jsonify({
        "status": "success",
        "count": len(resumes),
        "resumes": resumes,
        "grouped_by_role": grouped,
        "master_profile_status": master_profile.get("profile_status") if master_profile else "missing"
    }), 200


@resumes_bp.route("/<resume_id>", methods=["GET"])
@token_required
def get_single_resume(current_user, resume_id):
    """Retrieves a single resume by ID after verifying ownership."""
    try:
        oid = ObjectId(resume_id)
    except Exception:
        return jsonify({"status": "error", "message": "Invalid resume ID."}), 400

    resumes_col = get_resumes_collection()
    resume = resumes_col.find_one({"_id": oid, "user_id": str(current_user["_id"])})
    if not resume:
        return jsonify({"status": "error", "message": "Resume not found."}), 404

    profiles_col = get_profiles_collection()
    master_profile = profiles_col.find_one({"user_id": str(current_user["_id"])})
    master_updated_at = master_profile.get("updated_at") if master_profile else None

    return jsonify({
        "status": "success",
        "resume": serialize_resume(resume, master_updated_at)
    }), 200


@resumes_bp.route("/<resume_id>", methods=["PUT"])
@token_required
def update_existing_resume(current_user, resume_id):
    """Updates resume content/name/template with strict truthfulness validation."""
    data = request.get_json() or {}
    try:
        req = ResumeUpdateRequestSchema(**data)
    except ValidationError as e:
        return jsonify({
            "status": "error",
            "message": "Validation failed",
            "errors": e.errors()
        }), 400

    try:
        updated_resume, warnings = update_resume(
            user_id=current_user["_id"],
            resume_id=resume_id,
            update_data=req.model_dump(exclude_unset=True)
        )
        return jsonify({
            "status": "success",
            "message": "Resume updated and re-exported.",
            "resume": updated_resume,
            "warnings": warnings
        }), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Update failed: {str(e)}"}), 500


@resumes_bp.route("/<resume_id>/duplicate", methods=["POST"])
@token_required
def duplicate_existing_resume(current_user, resume_id):
    """Creates a new version from an existing resume."""
    try:
        new_resume = duplicate_resume(user_id=current_user["_id"], resume_id=resume_id)
        return jsonify({
            "status": "success",
            "message": f"Created new version {new_resume.get('version')}.",
            "resume": new_resume
        }), 201
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Duplication failed: {str(e)}"}), 500


@resumes_bp.route("/<resume_id>", methods=["DELETE"])
@token_required
def delete_single_resume(current_user, resume_id):
    """Deletes a resume and removes associated PDF/DOCX files."""
    try:
        success = delete_resume(user_id=current_user["_id"], resume_id=resume_id)
        if not success:
            return jsonify({"status": "error", "message": "Resume not found."}), 404
        return jsonify({
            "status": "success",
            "message": "Resume successfully deleted."
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Delete failed: {str(e)}"}), 500


@resumes_bp.route("/<resume_id>/download", methods=["GET"])
@token_required
def download_resume(current_user, resume_id):
    """
    Downloads the ATS-friendly PDF or DOCX file.
    Validates ownership before streaming the file.
    """
    format_type = request.args.get("format", "pdf").lower()
    try:
        file_path, download_filename, mime_type = get_resume_export_path(
            user_id=current_user["_id"],
            resume_id=resume_id,
            format_type=format_type
        )
        return send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=True,
            download_name=download_filename
        )
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Download failed: {str(e)}"}), 500

