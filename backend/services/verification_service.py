"""
Verification Service Orchestrator for CareerPilot AI (Module 6).
Coordinates multi-entity evidence checks for companies, recruiters, and job listings,
enforcing worst-of-three caution status logic, sample listing handling, and history tracking.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple

from backend.config import Config
from backend.database import get_job_verifications_collection, get_jobs_collection, get_user_reports_collection
from backend.services.ai_service import get_ai_service
from backend.services.verification.company_checks import run_company_checks
from backend.services.verification.recruiter_checks import run_recruiter_checks
from backend.services.verification.job_checks import run_job_posting_checks
from backend.models.verification import (
    JobVerificationSchema,
    EntityVerification,
    RecruiterVerification,
    serialize_verification,
    serialize_user_report
)


RECOMMENDED_ACTIONS = {
    "suspicious": "Do not share personal documents or pay any fee. Verify directly with the company through its official website.",
    "needs_verification": "Check the company's official careers page yourself before applying. Available evidence is incomplete.",
    "corroborated": "Evidence supports this posting. Still apply only through the official link and never pay a fee.",
    "not_applicable": "Sample listing: not a real vacancy, verification not applicable."
}


def evaluate_entity_status(evidence: List[Dict[str, Any]], warnings: List[Dict[str, Any]]) -> str:
    """
    Computes entity-level status based on hard evidence:
    - 'suspicious': At least one HIGH-severity warning.
    - 'corroborated': At least 2 independent PASS-type evidence items AND 0 HIGH warnings.
    - 'needs_verification': Everything else.
    """
    has_high_warning = any(w.get("severity") == "high" for w in warnings)
    if has_high_warning:
        return "suspicious"

    pass_evidence_count = sum(1 for e in evidence if e.get("result") == "pass")
    if pass_evidence_count >= 2:
        return "corroborated"

    return "needs_verification"


def compute_overall_status(
    company_status: str,
    recruiter_status: str,
    job_status: str,
    recruiter_provided: bool
) -> str:
    """
    Computes overall status using worst-of-three cautious logic:
    suspicious > needs_verification > corroborated.
    Company status NEVER upgrades recruiter or job status.
    """
    # Evaluate entities
    evaluated_statuses = [company_status, job_status]
    if recruiter_provided:
        evaluated_statuses.append(recruiter_status)

    if any(s == "suspicious" for s in evaluated_statuses):
        return "suspicious"
    if any(s == "needs_verification" for s in evaluated_statuses):
        return "needs_verification"
    if all(s == "corroborated" for s in evaluated_statuses):
        return "corroborated"

    return "needs_verification"


def run_full_verification(
    job_doc: Dict[str, Any],
    recruiter_override: Optional[Dict[str, Any]] = None,
    allow_test_scenarios: bool = False
) -> Dict[str, Any]:
    """
    Runs full verification for a job posting across company, recruiter, and job.
    Enforces sample job bypass unless marked as test scenario.
    """
    job_id = job_doc.get("job_id")
    is_sample = job_doc.get("is_sample", False)
    is_test_scenario = job_doc.get("is_test_scenario", False) or allow_test_scenarios
    now = datetime.now(timezone.utc)
    ttl_hours = Config.VERIFICATION_CACHE_TTL_HOURS
    next_check = now + timedelta(hours=ttl_hours)

    # 1. Standard Sample Listing Handling (Zero Fabricated Evidence)
    if is_sample and not is_test_scenario:
        return {
            "job_id": job_id,
            "company": {
                "status": "not_applicable",
                "evidence": [],
                "missing": [],
                "warnings": []
            },
            "recruiter": {
                "status": "not_applicable",
                "provided": False,
                "contact": {},
                "evidence": [],
                "missing": [],
                "warnings": []
            },
            "job": {
                "status": "not_applicable",
                "evidence": [],
                "missing": [],
                "warnings": []
            },
            "overall_status": "not_applicable",
            "recommended_action": RECOMMENDED_ACTIONS["not_applicable"],
            "checked_at": now,
            "next_check_after": next_check,
            "checks_run": [],
            "checks_skipped": [
                {
                    "name": "sample_listing_bypass",
                    "reason": "Sample listing: not a real vacancy, verification not applicable."
                }
            ],
            "verification_history": []
        }

    # 2. Company Checks
    company_name = job_doc.get("company", "")
    application_url = job_doc.get("application_url", "")
    company_ev, company_missing, company_warnings = run_company_checks(company_name, application_url)
    company_status = evaluate_entity_status(company_ev, company_warnings)

    # 3. Recruiter Checks
    rec_name = (recruiter_override.get("name") if recruiter_override else None) or job_doc.get("recruiter_name")
    rec_email = (recruiter_override.get("email") if recruiter_override else None) or job_doc.get("recruiter_email")
    rec_company = (recruiter_override.get("claimed_company") if recruiter_override else None)

    provided, contact_dict, rec_ev, rec_missing, rec_warnings = run_recruiter_checks(
        company_name=company_name,
        application_url=application_url,
        recruiter_name=rec_name,
        recruiter_email=rec_email,
        claimed_company=rec_company
    )
    recruiter_status = evaluate_entity_status(rec_ev, rec_warnings) if provided else "needs_verification"

    # 4. Job Posting Checks
    ai_service = get_ai_service()
    job_ev, job_missing, job_warnings = run_job_posting_checks(job_doc, ai_service=ai_service)
    job_status = evaluate_entity_status(job_ev, job_warnings)

    # 5. Overall Status & Recommended Action
    overall_status = compute_overall_status(
        company_status=company_status,
        recruiter_status=recruiter_status,
        job_status=job_status,
        recruiter_provided=provided
    )
    recommended_action = RECOMMENDED_ACTIONS.get(overall_status, RECOMMENDED_ACTIONS["needs_verification"])

    checks_run = [
        "https_enforcement",
        "ats_allowlist_match",
        "scam_indicator_scan",
        "description_completeness"
    ]
    if provided:
        checks_run.append("recruiter_contact_verification")

    return {
        "job_id": job_id,
        "company": {
            "status": company_status,
            "evidence": company_ev,
            "missing": company_missing,
            "warnings": company_warnings
        },
        "recruiter": {
            "status": recruiter_status,
            "provided": provided,
            "contact": contact_dict,
            "evidence": rec_ev,
            "missing": rec_missing,
            "warnings": rec_warnings
        },
        "job": {
            "status": job_status,
            "evidence": job_ev,
            "missing": job_missing,
            "warnings": job_warnings
        },
        "overall_status": overall_status,
        "recommended_action": recommended_action,
        "checked_at": now,
        "next_check_after": next_check,
        "checks_run": checks_run,
        "checks_skipped": [],
        "verification_history": []
    }


def get_or_compute_job_verification(job_id: str, force_recompute: bool = False) -> Dict[str, Any]:
    """
    Retrieves latest verification for job_id or computes a new one.
    Auto-refreshes if cached verification has expired.
    """
    verif_coll = get_job_verifications_collection()
    jobs_coll = get_jobs_collection()

    job_doc = jobs_coll.find_one({"job_id": job_id})
    if not job_doc:
        raise ValueError(f"Job not found for job_id '{job_id}'")

    existing_verif = verif_coll.find_one({"job_id": job_id})
    now = datetime.now(timezone.utc)

    # Check cache validity
    if existing_verif and not force_recompute:
        next_check = existing_verif.get("next_check_after")
        if isinstance(next_check, datetime):
            if next_check.tzinfo is None:
                next_check = next_check.replace(tzinfo=timezone.utc)
            if now < next_check:
                return serialize_verification(existing_verif)

    # Compute new verification
    new_verif = run_full_verification(job_doc)

    # Preserve history (keep last 5)
    history = []
    if existing_verif:
        history = list(existing_verif.get("verification_history", []))
        prev_run = {
            "checked_at": existing_verif.get("checked_at", now),
            "overall_status": existing_verif.get("overall_status", "unknown"),
            "company_status": existing_verif.get("company", {}).get("status"),
            "recruiter_status": existing_verif.get("recruiter", {}).get("status"),
            "job_status": existing_verif.get("job", {}).get("status")
        }
        history.insert(0, prev_run)
        history = history[:5]

    new_verif["verification_history"] = history

    # Upsert to MongoDB
    verif_coll.update_one(
        {"job_id": job_id},
        {"$set": new_verif},
        upsert=True
    )

    saved_doc = verif_coll.find_one({"job_id": job_id})
    return serialize_verification(saved_doc)


def submit_recruiter_details_and_recompute(
    job_id: str,
    contact_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Processes candidate-entered recruiter contact details and re-runs recruiter checks.
    """
    verif_coll = get_job_verifications_collection()
    jobs_coll = get_jobs_collection()

    job_doc = jobs_coll.find_one({"job_id": job_id})
    if not job_doc:
        raise ValueError(f"Job not found for job_id '{job_id}'")

    existing_verif = verif_coll.find_one({"job_id": job_id})

    # Run verification with recruiter override
    new_verif = run_full_verification(
        job_doc,
        recruiter_override=contact_data,
        allow_test_scenarios=True
    )

    # Preserve history
    history = []
    if existing_verif:
        history = list(existing_verif.get("verification_history", []))
        prev_run = {
            "checked_at": existing_verif.get("checked_at", datetime.now(timezone.utc)),
            "overall_status": existing_verif.get("overall_status", "unknown"),
            "company_status": existing_verif.get("company", {}).get("status"),
            "recruiter_status": existing_verif.get("recruiter", {}).get("status"),
            "job_status": existing_verif.get("job", {}).get("status")
        }
        history.insert(0, prev_run)
        history = history[:5]

    new_verif["verification_history"] = history

    verif_coll.update_one(
        {"job_id": job_id},
        {"$set": new_verif},
        upsert=True
    )

    saved_doc = verif_coll.find_one({"job_id": job_id})
    return serialize_verification(saved_doc)


def submit_user_report(
    user_id: str,
    job_id: str,
    reason: str,
    note: str = ""
) -> Dict[str, Any]:
    """
    Stores candidate abuse/scam reports in user_reports collection.
    Scattered solely for candidate security auditing; never posted publicly.
    """
    reports_coll = get_user_reports_collection()
    jobs_coll = get_jobs_collection()

    job_doc = jobs_coll.find_one({"job_id": job_id})
    if not job_doc:
        raise ValueError(f"Job not found for job_id '{job_id}'")

    report_doc = {
        "user_id": user_id,
        "job_id": job_id,
        "reason": reason,
        "note": (note or "").strip()[:1000],
        "created_at": datetime.now(timezone.utc)
    }

    res = reports_coll.insert_one(report_doc)
    saved_report = reports_coll.find_one({"_id": res.inserted_id})
    return serialize_user_report(saved_report)


def list_user_verifications(status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Lists job verifications filtered by status.
    """
    verif_coll = get_job_verifications_collection()
    jobs_coll = get_jobs_collection()

    query = {}
    if status and status in ("corroborated", "needs_verification", "suspicious", "not_applicable"):
        query["overall_status"] = status

    cursor = verif_coll.find(query).sort("checked_at", -1).limit(limit)
    verifs = []
    for doc in cursor:
        serialized = serialize_verification(doc)
        # Attach basic job metadata
        job_meta = jobs_coll.find_one({"job_id": doc.get("job_id")}, {"title": 1, "company": 1, "location": 1})
        if job_meta:
            serialized["job_title"] = job_meta.get("title")
            serialized["company_name"] = job_meta.get("company")
            serialized["location"] = job_meta.get("location")
        verifs.append(serialized)

    return verifs
