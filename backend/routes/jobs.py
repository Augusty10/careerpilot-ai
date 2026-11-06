"""
Job Discovery and Management Routes (Module 4).
Protected endpoints for job discovery, filtering, details, bookmarking, and preference management.
"""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from backend.services.auth_service import token_required
from backend.limiter import limiter
from backend.models.job import (
    JobDiscoverRequestSchema,
    DiscoveryPreferencesSchema,
    SaveJobRequestSchema
)
from backend.services.job_sources.registry import source_registry
from backend.services.job_service import (
    run_job_discovery,
    get_jobs_feed,
    get_job_by_id,
    save_job,
    unsave_job,
    get_saved_jobs,
    update_discovery_preferences
)


jobs_bp = Blueprint("jobs", __name__, url_prefix="/api/jobs")


@jobs_bp.route("/sources", methods=["GET"])
@token_required
def get_sources_status(current_user):
    """Returns active and enabled job source adapters."""
    sources = source_registry.get_sources_info()
    return jsonify({
        "status": "success",
        "sources": sources
    }), 200


@jobs_bp.route("/discover", methods=["POST"])
@token_required
@limiter.limit("10 per minute")
def discover_jobs(current_user):
    """
    Executes a job discovery run across enabled sources.
    Rate limited to 10 requests per minute per candidate.
    """
    data = request.get_json() or {}
    try:
        req = JobDiscoverRequestSchema(**data)
    except ValidationError as e:
        return jsonify({
            "status": "error",
            "message": "Invalid discovery parameters",
            "errors": e.errors()
        }), 400

    try:
        summary = run_job_discovery(
            user_id=current_user["_id"],
            discovery_params=req.model_dump(exclude_unset=True)
        )
        return jsonify({
            "status": "success",
            "message": f"Discovery complete: {summary['stored']} jobs processed.",
            "summary": summary
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Job discovery failed: {str(e)}"
        }), 500


@jobs_bp.route("", methods=["GET"])
@token_required
def list_jobs(current_user):
    """
    Retrieves a paginated, filterable feed of job postings.
    Supports query parameters for role, location, work_mode, job_type, fresher_only, etc.
    """
    try:
        feed = get_jobs_feed(
            user_id=current_user["_id"],
            query_params=request.args.to_dict()
        )
        return jsonify({
            "status": "success",
            **feed
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve jobs feed: {str(e)}"
        }), 500


@jobs_bp.route("/<job_id>", methods=["GET"])
@token_required
def get_single_job(current_user, job_id):
    """Retrieves full details for a single job posting."""
    job = get_job_by_id(user_id=current_user["_id"], job_id=job_id)
    if not job:
        return jsonify({
            "status": "error",
            "message": "Job posting not found."
        }), 404

    return jsonify({
        "status": "success",
        "job": job
    }), 200


@jobs_bp.route("/<job_id>/save", methods=["POST"])
@token_required
def bookmark_job(current_user, job_id):
    """Saves/bookmarks a job posting for the logged-in candidate."""
    data = request.get_json() or {}
    try:
        req = SaveJobRequestSchema(**data)
    except ValidationError as e:
        return jsonify({
            "status": "error",
            "message": "Validation error",
            "errors": e.errors()
        }), 400

    try:
        res = save_job(user_id=current_user["_id"], job_id=job_id, notes=req.notes or "")
        return jsonify(res), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to save job: {str(e)}"}), 500


@jobs_bp.route("/<job_id>/save", methods=["DELETE"])
@token_required
def remove_saved_job(current_user, job_id):
    """Removes a job posting from the candidate's saved list."""
    try:
        success = unsave_job(user_id=current_user["_id"], job_id=job_id)
        if not success:
            return jsonify({"status": "error", "message": "Job was not in saved list."}), 404

        return jsonify({
            "status": "success",
            "message": "Job removed from saved list."
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to unsave job: {str(e)}"}), 500


@jobs_bp.route("/saved", methods=["GET"])
@token_required
def list_saved_jobs(current_user):
    """Retrieves all jobs saved by the authenticated candidate."""
    try:
        saved_list = get_saved_jobs(user_id=current_user["_id"])
        return jsonify({
            "status": "success",
            "count": len(saved_list),
            "saved_jobs": saved_list
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve saved jobs: {str(e)}"
        }), 500


@jobs_bp.route("/preferences", methods=["PUT"])
@token_required
def update_preferences(current_user):
    """Updates candidate discovery preferences on their Master Profile."""
    data = request.get_json() or {}
    try:
        req = DiscoveryPreferencesSchema(**data)
    except ValidationError as e:
        return jsonify({
            "status": "error",
            "message": "Validation error",
            "errors": e.errors()
        }), 400

    try:
        updated_prefs = update_discovery_preferences(
            user_id=current_user["_id"],
            prefs_data=req.model_dump()
        )
        return jsonify({
            "status": "success",
            "message": "Job discovery preferences updated.",
            "preferences": updated_prefs
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to update preferences: {str(e)}"
        }), 500

