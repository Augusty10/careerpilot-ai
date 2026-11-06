from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from bson import ObjectId

from backend.services.auth_service import token_required
from backend.models.match import BatchMatchRequestSchema
from backend.database import get_job_matches_collection, get_jobs_collection
from backend.services.matching_service import (
    compute_match,
    compute_batch_matches,
    get_recommended_jobs
)


matching_bp = Blueprint("matching", __name__, url_prefix="/api")


@matching_bp.route("/matches/<job_id>", methods=["POST"])
@token_required
def calculate_match_endpoint(current_user, job_id):
    """
    Computes or recomputes the transparent match and eligibility result
    between the logged-in candidate's approved master profile and a job listing.
    """
    user_id = str(current_user["_id"])
    force_param = request.args.get("force", "true").lower() in ("true", "1", "yes")

    try:
        match_result = compute_match(
            user_id=user_id,
            job_id=job_id,
            force_recompute=force_param
        )
        return jsonify({
            "status": "success",
            "message": "Match evaluation computed successfully.",
            "match": match_result
        }), 200
    except ValueError as val_err:
        return jsonify({
            "status": "error",
            "message": str(val_err)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to compute job match: {str(e)}"
        }), 500


@matching_bp.route("/matches/batch", methods=["POST"])
@token_required
def batch_match_endpoint(current_user):
    """
    Batch computes or retrieves match scores for up to 50 jobs.
    Enforces maximum batch size limit.
    """
    data = request.get_json() or {}
    try:
        req = BatchMatchRequestSchema(**data)
    except ValidationError as e:
        return jsonify({
            "status": "error",
            "message": "Invalid batch request. Ensure 'job_ids' is a list of 1 to 50 job IDs.",
            "errors": e.errors()
        }), 400

    user_id = str(current_user["_id"])
    try:
        results = compute_batch_matches(user_id=user_id, job_ids=req.job_ids)
        return jsonify({
            "status": "success",
            "count": len(results),
            "matches": results
        }), 200
    except ValueError as val_err:
        return jsonify({
            "status": "error",
            "message": str(val_err)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to compute batch matches: {str(e)}"
        }), 500


@matching_bp.route("/matches/<job_id>", methods=["GET"])
@token_required
def get_match_endpoint(current_user, job_id):
    """
    Retrieves the stored match evaluation for a job.
    If not yet computed, computes it automatically.
    If the candidate's master profile has changed since computation, returns is_stale=True.
    """
    user_id = str(current_user["_id"])
    auto_recompute = request.args.get("recompute_if_stale", "false").lower() in ("true", "1", "yes")

    try:
        match_result = compute_match(
            user_id=user_id,
            job_id=job_id,
            force_recompute=auto_recompute
        )
        return jsonify({
            "status": "success",
            "match": match_result
        }), 200
    except ValueError as val_err:
        return jsonify({
            "status": "error",
            "message": str(val_err)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve match: {str(e)}"
        }), 500


@matching_bp.route("/matches", methods=["GET"])
@token_required
def list_my_matches(current_user):
    """
    Lists the candidate's computed matches with optional filtering by category or minimum skill coverage.
    """
    user_id = current_user["_id"]
    user_oid = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id

    category = request.args.get("category")
    min_coverage = request.args.get("min_coverage")
    sort_by = request.args.get("sort", "recent")

    query: dict = {"$or": [{"user_id": user_oid}, {"user_id": str(user_id)}]}

    if category:
        query["category"] = category

    if min_coverage:
        try:
            query["skill_coverage"] = {"$gte": float(min_coverage)}
        except ValueError:
            pass

    matches_col = get_job_matches_collection()
    cursor = matches_col.find(query)

    if sort_by == "coverage":
        cursor = cursor.sort("skill_coverage", -1)
    else:
        cursor = cursor.sort("computed_at", -1)

    raw_matches = list(cursor.limit(100))

    from backend.models.match import serialize_match
    serialized = [serialize_match(doc) for doc in raw_matches]

    return jsonify({
        "status": "success",
        "count": len(serialized),
        "matches": serialized
    }), 200


@matching_bp.route("/jobs/recommended", methods=["GET"])
@token_required
def recommended_jobs_endpoint(current_user):
    """
    Returns active job opportunities ranked by match category and skill coverage.
    Excludes expired jobs and not_eligible jobs by default.
    """
    user_id = str(current_user["_id"])
    category = request.args.get("category")
    min_cov_raw = request.args.get("min_coverage")
    min_coverage = float(min_cov_raw) if min_cov_raw else None

    exclude_not_eligible = request.args.get("exclude_not_eligible", "true").lower() in ("true", "1", "yes")
    sort_by = request.args.get("sort_by", "rank")
    page = max(1, int(request.args.get("page", 1)))
    limit = min(50, max(1, int(request.args.get("limit", 15))))

    try:
        rec_data = get_recommended_jobs(
            user_id=user_id,
            category=category,
            min_coverage=min_coverage,
            exclude_not_eligible=exclude_not_eligible,
            sort_by=sort_by,
            page=page,
            limit=limit
        )
        return jsonify({
            "status": "success",
            **rec_data
        }), 200
    except ValueError as val_err:
        return jsonify({
            "status": "error",
            "message": str(val_err)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve recommended jobs: {str(e)}"
        }), 500

