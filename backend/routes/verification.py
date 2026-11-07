"""
Verification Routes for CareerPilot AI (Module 6).
Provides protected endpoints for running multi-entity legitimacy checks, retrieving evidence reports,
submitting recruiter contact details, and reporting suspicious postings.
"""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from backend.services.auth_service import token_required
from backend.limiter import limiter
from backend.models.verification import (
    SubmitRecruiterDetailsSchema,
    UserReportCreateSchema,
    serialize_verification
)
from backend.services.verification_service import (
    get_or_compute_job_verification,
    submit_recruiter_details_and_recompute,
    submit_user_report,
    list_user_verifications
)


verification_bp = Blueprint("verification", __name__, url_prefix="/api/verification")


@verification_bp.route("/<job_id>", methods=["POST"])
@token_required
@limiter.limit("30 per minute")
def run_verification_endpoint(current_user, job_id):
    """
    Triggers or forces recomputation of multi-entity verification report for a job posting.
    """
    try:
        report = get_or_compute_job_verification(job_id=job_id, force_recompute=True)
        return jsonify({
            "status": "success",
            "message": "Verification report computed successfully.",
            "verification": report
        }), 200
    except ValueError as val_err:
        return jsonify({
            "status": "error",
            "message": str(val_err)
        }), 404
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Verification failed: {str(e)}"
        }), 500


@verification_bp.route("/<job_id>", methods=["GET"])
@token_required
def get_verification_endpoint(current_user, job_id):
    """
    Retrieves the latest verification report for a job posting (auto-refreshes if older than TTL).
    """
    try:
        report = get_or_compute_job_verification(job_id=job_id, force_recompute=False)
        return jsonify({
            "status": "success",
            "verification": report
        }), 200
    except ValueError as val_err:
        return jsonify({
            "status": "error",
            "message": str(val_err)
        }), 404
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve verification: {str(e)}"
        }), 500


@verification_bp.route("/<job_id>/recruiter", methods=["PUT"])
@token_required
@limiter.limit("20 per minute")
def submit_recruiter_endpoint(current_user, job_id):
    """
    Allows a candidate to submit recruiter contact details they received,
    re-running recruiter-specific verification checks.
    """
    payload = request.get_json() or {}
    try:
        contact_validated = SubmitRecruiterDetailsSchema(**payload)
    except ValidationError as val_err:
        return jsonify({
            "status": "error",
            "message": "Invalid recruiter details submitted.",
            "errors": val_err.errors()
        }), 400

    try:
        updated_report = submit_recruiter_details_and_recompute(
            job_id=job_id,
            contact_data=contact_validated.model_dump()
        )
        return jsonify({
            "status": "success",
            "message": "Recruiter verification completed.",
            "verification": updated_report
        }), 200
    except ValueError as val_err:
        return jsonify({
            "status": "error",
            "message": str(val_err)
        }), 404
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to recompute recruiter verification: {str(e)}"
        }), 500


@verification_bp.route("/<job_id>/report", methods=["POST"])
@token_required
@limiter.limit("10 per minute")
def report_job_endpoint(current_user, job_id):
    """
    Allows candidate to submit a security/abuse report regarding a suspicious job vacancy.
    """
    user_id = str(current_user["_id"])
    payload = request.get_json() or {}

    try:
        validated_report = UserReportCreateSchema(**payload)
    except ValidationError as val_err:
        return jsonify({
            "status": "error",
            "message": "Invalid report payload.",
            "errors": val_err.errors()
        }), 400

    try:
        report_record = submit_user_report(
            user_id=user_id,
            job_id=job_id,
            reason=validated_report.reason,
            note=validated_report.note
        )
        return jsonify({
            "status": "success",
            "message": "Thank you for reporting this posting. Our safety team will review it.",
            "report": report_record
        }), 201
    except ValueError as val_err:
        return jsonify({
            "status": "error",
            "message": str(val_err)
        }), 404
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to submit report: {str(e)}"
        }), 500


@verification_bp.route("", methods=["GET"])
@token_required
def list_verifications_endpoint(current_user):
    """
    Lists previously verified jobs, optionally filtered by overall_status.
    """
    status_filter = request.args.get("status")
    limit = min(int(request.args.get("limit", 50)), 100)

    try:
        verifs = list_user_verifications(status=status_filter, limit=limit)
        return jsonify({
            "status": "success",
            "verifications": verifs,
            "count": len(verifs)
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to list verifications: {str(e)}"
        }), 500
