import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from bson import ObjectId

from backend.config import Config
from backend.database import get_db, get_profiles_collection, get_jobs_collection, get_job_matches_collection
from backend.models.match import JobMatchSchema, serialize_match
from backend.services.ai_service import get_ai_service
from backend.services.eligibility_rules import (
    check_education_qualification,
    check_graduation_year,
    check_experience_requirement,
    check_location_preference,
    check_job_type_preference,
    check_certifications_requirement,
    extract_candidate_skills_set,
    evaluate_skills_and_coverage,
    determine_match_category
)


def compute_profile_version_hash(profile: Dict[str, Any]) -> str:
    """Computes a stable hash of profile attributes relevant to job matching."""
    relevant_payload = {
        "skills": profile.get("skills", {}),
        "education": [
            {
                "degree": e.get("degree", "").strip().lower(),
                "institution": e.get("institution", "").strip().lower(),
                "graduation_year": e.get("graduation_year"),
                "score": e.get("score")
            }
            for e in profile.get("education", [])
        ],
        "work_experience": [
            {
                "company": w.get("company", "").strip().lower(),
                "role": w.get("role", "").strip().lower(),
                "start_date": w.get("start_date", ""),
                "end_date": w.get("end_date", "")
            }
            for w in profile.get("work_experience", [])
        ],
        "internships": [
            {
                "company": i.get("company", "").strip().lower(),
                "role": i.get("role", "").strip().lower(),
                "start_date": i.get("start_date", ""),
                "end_date": i.get("end_date", "")
            }
            for i in profile.get("internships", [])
        ],
        "certifications": [
            c.get("name", "").strip().lower() for c in profile.get("certifications", [])
        ],
        "preferred_locations": [
            loc.strip().lower() for loc in profile.get("preferred_locations", [])
        ],
        "preferred_roles": [
            r.strip().lower() for r in profile.get("preferred_roles", [])
        ]
    }
    raw_str = json.dumps(relevant_payload, sort_keys=True)
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:16]


def compute_match(
    user_id: str,
    job_id: str,
    force_recompute: bool = False,
    db: Any = None
) -> Dict[str, Any]:
    """
    Computes or retrieves transparent eligibility and match evaluation
    between a candidate's approved master profile and a job listing.
    """
    profiles_col = get_profiles_collection(db)
    jobs_col = get_jobs_collection(db)
    matches_col = get_job_matches_collection(db)

    # 1. Fetch Candidate Profile & Verify Approval
    user_oid = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id
    profile = profiles_col.find_one({"user_id": user_oid})
    if not profile:
        profile = profiles_col.find_one({"user_id": str(user_id)})

    if not profile:
        raise ValueError("Candidate profile not found. Please create your Master Profile first.")

    # 2. Fetch Job Posting
    job = jobs_col.find_one({"job_id": job_id})
    if not job:
        raise ValueError(f"Job with ID '{job_id}' not found.")

    current_hash = compute_profile_version_hash(profile)

    # 3. Check for existing cached match
    existing_match = matches_col.find_one({"user_id": user_oid, "job_id": job_id})
    if not existing_match:
        existing_match = matches_col.find_one({"user_id": str(user_id), "job_id": job_id})

    # If profile is not approved:
    if profile.get("profile_status") != "approved":
        if existing_match:
            # If an existing match was computed previously, allow viewing it with is_stale=True
            return serialize_match(existing_match, is_stale=True)
        raise ValueError("Job matching requires an approved master profile. Please review and approve your profile first.")

    if existing_match and not force_recompute:
        stored_hash = existing_match.get("profile_version_hash")
        is_stale = (stored_hash != current_hash)
        if not is_stale:
            return serialize_match(existing_match, is_stale=False)
        else:
            # If stale, we return the cached match flagged as is_stale=True
            # so the UI can display the out-of-date banner and Recompute button
            return serialize_match(existing_match, is_stale=True)

    # 4. Perform Deterministic Matching
    hard_failures: List[str] = []
    warnings: List[str] = []

    # (a) Candidate Skills
    cand_skills_set = extract_candidate_skills_set(profile)
    job_req_skills = job.get("required_skills", []) or []

    # Unmatched skills check via AI/Deterministic lookup
    unmatched_initial = [
        s for s in job_req_skills
        if s.strip().lower() not in cand_skills_set
    ]

    ai_service = get_ai_service()
    related_skills_dict = ai_service.check_related_skills(
        unmatched_job_skills=unmatched_initial,
        candidate_skills=list(cand_skills_set)
    )

    matched_skills, related_skills, missing_skills, skill_coverage = evaluate_skills_and_coverage(
        candidate_skills=cand_skills_set,
        job_required_skills=job_req_skills,
        semantic_related_dict=related_skills_dict
    )

    # (b) Education Qualification
    edu_status, edu_job_req, edu_cand_val, edu_hard_fail = check_education_qualification(
        candidate_education=profile.get("education", []),
        job_education_text=job.get("education_required")
    )
    if edu_hard_fail:
        hard_failures.append(f"Educational requirement not met (Job requires: {edu_job_req}, You have: {edu_cand_val})")

    # (c) Graduation Year / Batch Eligibility
    grad_status, grad_job_req, grad_cand_val, grad_hard_fail = check_graduation_year(
        candidate_education=profile.get("education", []),
        job_description=job.get("description"),
        job_title=job.get("title")
    )
    if grad_hard_fail:
        hard_failures.append(f"Graduation batch year not met (Job requires: {grad_job_req}, Your year: {grad_cand_val})")

    # (d) Experience Requirements
    exp_status, exp_job_req, exp_cand_val, exp_hard_fail = check_experience_requirement(
        work_experience=profile.get("work_experience", []),
        internships=profile.get("internships", []),
        job_min_years=job.get("experience_min_years"),
        job_max_years=job.get("experience_max_years"),
        job_fresher_status=job.get("fresher_status"),
        job_experience_text=job.get("experience_text")
    )
    if exp_hard_fail:
        hard_failures.append(f"Experience requirement not met (Job requires: {exp_job_req}, You have: {exp_cand_val})")

    # (e) Location & Work Mode Preferences
    loc_status, loc_job_req, loc_cand_val, loc_warning = check_location_preference(
        candidate_preferred_locations=profile.get("preferred_locations", []),
        job_location=job.get("location"),
        job_work_mode=job.get("work_mode")
    )
    if loc_warning:
        warnings.append(loc_warning)

    # (f) Job Type
    type_status, type_job_req, type_cand_val, type_warning = check_job_type_preference(
        candidate_preferred_roles=profile.get("preferred_roles", []),
        job_type=job.get("job_type")
    )
    if type_warning:
        warnings.append(type_warning)

    # (g) Certifications
    cert_status, cert_missing, cert_job_req, cert_hard_fail = check_certifications_requirement(
        candidate_certifications=profile.get("certifications", []),
        job_description=job.get("description")
    )
    if cert_hard_fail and cert_missing:
        hard_failures.append(f"Mandatory certification(s) missing: {', '.join(cert_missing)}")

    # (h) Category Decision
    category = determine_match_category(
        hard_failures=hard_failures,
        skill_coverage=skill_coverage,
        total_required_skills=len(job_req_skills),
        strong_threshold=Config.MATCH_STRONG_THRESHOLD,
        partial_threshold=Config.MATCH_PARTIAL_THRESHOLD
    )

    if not job_req_skills:
        warnings.append("Job has limited information on specific required technical skills.")

    # (i) Structured Payload for Explanation & Persistence
    match_doc = {
        "user_id": user_oid,
        "job_id": job_id,
        "profile_version_hash": current_hash,
        "category": category,
        "skill_coverage": skill_coverage,
        "skills": {
            "matched": matched_skills,
            "related": related_skills,
            "missing": missing_skills,
            "total_required": len(job_req_skills),
            "raw_job_skills": job_req_skills
        },
        "education": {
            "status": edu_status,
            "job_requirement": edu_job_req,
            "candidate_value": edu_cand_val
        },
        "graduation_year": {
            "status": grad_status,
            "job_requirement": grad_job_req,
            "candidate_value": grad_cand_val
        },
        "experience": {
            "status": exp_status,
            "job_requirement": exp_job_req,
            "candidate_value": exp_cand_val
        },
        "location": {
            "status": loc_status,
            "job_requirement": loc_job_req,
            "candidate_value": loc_cand_val
        },
        "job_type": {
            "status": type_status,
            "job_requirement": type_job_req,
            "candidate_value": type_cand_val
        },
        "certifications": {
            "status": cert_status,
            "missing": cert_missing,
            "job_requirement": cert_job_req
        },
        "hard_failures": hard_failures,
        "warnings": warnings,
        "explanation": "",
        "explanation_source": "ai" if not Config.AI_MOCK_MODE and Config.GEMINI_API_KEY else "rules",
        "computed_at": datetime.now(timezone.utc)
    }

    # (j) Generate Plain-Language Explanation
    explanation = ai_service.generate_match_explanation(match_doc)
    match_doc["explanation"] = explanation

    # (k) Upsert to MongoDB
    matches_col.update_one(
        {"user_id": user_oid, "job_id": job_id},
        {"$set": match_doc},
        upsert=True
    )

    saved_doc = matches_col.find_one({"user_id": user_oid, "job_id": job_id})
    return serialize_match(saved_doc or match_doc, is_stale=False)


def compute_batch_matches(
    user_id: str,
    job_ids: List[str],
    db: Any = None
) -> List[Dict[str, Any]]:
    """Computes or retrieves match results for up to 50 jobs."""
    if not job_ids:
        return []

    if len(job_ids) > 50:
        raise ValueError("Batch matching cannot exceed 50 jobs per request.")

    results: List[Dict[str, Any]] = []
    for jid in job_ids:
        try:
            m = compute_match(user_id=user_id, job_id=jid, force_recompute=False, db=db)
            results.append(m)
        except Exception:
            # Shield individual failures
            pass

    return results


def get_recommended_jobs(
    user_id: str,
    category: Optional[str] = None,
    min_coverage: Optional[float] = None,
    exclude_not_eligible: bool = True,
    sort_by: str = "rank",
    page: int = 1,
    limit: int = 20,
    db: Any = None
) -> Dict[str, Any]:
    """
    Retrieves active jobs ranked by match category and skill coverage.
    Excludes expired jobs and optionally excludes 'not_eligible' opportunities.
    """
    jobs_col = get_jobs_collection(db)
    matches_col = get_job_matches_collection(db)

    user_oid = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id

    # 1. Fetch active, non-expired jobs
    active_jobs_cursor = jobs_col.find({"status": "active"}).sort("posted_at", -1).limit(100)
    active_jobs = list(active_jobs_cursor)

    if not active_jobs:
        return {
            "jobs": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "stats": {"strong_match": 0, "partial_match": 0, "low_match": 0, "not_eligible": 0}
        }

    # 2. Ensure matches exist for active jobs
    job_ids = [j["job_id"] for j in active_jobs]
    existing_matches = {
        m["job_id"]: m for m in matches_col.find({"user_id": user_oid, "job_id": {"$in": job_ids}})
    }

    # For any active job without a match record, compute on-the-fly
    for job in active_jobs:
        jid = job["job_id"]
        if jid not in existing_matches:
            try:
                m = compute_match(user_id=user_id, job_id=jid, force_recompute=False, db=db)
                existing_matches[jid] = m
            except Exception:
                pass

    # 3. Category Rank Mapping
    rank_weights = {
        "strong_match": 4,
        "partial_match": 3,
        "low_match": 2,
        "not_eligible": 1
    }

    # 4. Filter and Aggregate Stats
    category_counts = {
        "strong_match": 0,
        "partial_match": 0,
        "low_match": 0,
        "not_eligible": 0
    }

    enriched_jobs = []
    for job in active_jobs:
        jid = job["job_id"]
        match_info = existing_matches.get(jid)
        if not match_info:
            continue

        cat = match_info.get("category", "low_match")
        category_counts[cat] = category_counts.get(cat, 0) + 1

        # Apply Filters
        if exclude_not_eligible and cat == "not_eligible":
            continue

        if category and cat != category:
            continue

        cov = match_info.get("skill_coverage")
        if min_coverage is not None and (cov is None or cov < min_coverage):
            continue

        # Clean job representation
        enriched_jobs.append({
            "job": {
                "job_id": job.get("job_id"),
                "title": job.get("title"),
                "company": job.get("company"),
                "location": job.get("location"),
                "work_mode": job.get("work_mode"),
                "job_type": job.get("job_type"),
                "fresher_status": job.get("fresher_status"),
                "experience_text": job.get("experience_text"),
                "required_skills": job.get("required_skills", []),
                "is_sample": job.get("is_sample", False),
                "application_url": job.get("application_url"),
                "posted_at": job.get("posted_at")
            },
            "match": {
                "category": cat,
                "skill_coverage": cov,
                "matched_skills": match_info.get("skills", {}).get("matched", []),
                "missing_skills": match_info.get("skills", {}).get("missing", []),
                "explanation": match_info.get("explanation", ""),
                "is_stale": match_info.get("is_stale", False)
            },
            "_rank": rank_weights.get(cat, 0),
            "_coverage": cov if cov is not None else 0.0
        })

    # 5. Sort
    if sort_by == "coverage":
        enriched_jobs.sort(key=lambda x: x["_coverage"], reverse=True)
    elif sort_by == "recent":
        enriched_jobs.sort(key=lambda x: str(x["job"].get("posted_at") or ""), reverse=True)
    else:  # default "rank"
        enriched_jobs.sort(key=lambda x: (x["_rank"], x["_coverage"]), reverse=True)

    # 6. Pagination
    total = len(enriched_jobs)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_items = enriched_jobs[start_idx:end_idx]

    # Remove temporary sort keys
    cleaned_items = [
        {"job": item["job"], "match": item["match"]} for item in paginated_items
    ]

    return {
        "jobs": cleaned_items,
        "total": total,
        "page": page,
        "limit": limit,
        "stats": category_counts
    }
