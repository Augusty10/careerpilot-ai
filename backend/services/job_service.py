"""
Job Service.
Coordinates discovery execution, job feed filtering, pagination,
per-user saved jobs pipeline, and candidate discovery preferences.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import math
from bson import ObjectId

from backend.config import Config
from backend.database import get_jobs_collection, get_saved_jobs_collection, get_profiles_collection
from backend.services.job_sources.registry import source_registry
from backend.services.job_normalizer import normalize_job_dict
from backend.services.dedup_service import detect_and_link_duplicates, apply_expiration_check
from backend.models.job import serialize_job


def run_job_discovery(user_id: str, discovery_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Executes an authorized job discovery run across active sources.
    Defaults search keywords and locations to the candidate's master profile preferences.
    Normalizes data, flags duplicates and expired listings, and persists to the database.
    """
    profiles_col = get_profiles_collection()
    jobs_col = get_jobs_collection()

    master_profile = profiles_col.find_one({"user_id": str(user_id)}) or {}
    params = discovery_params or {}

    # Query resolution
    roles = params.get("roles") or master_profile.get("preferred_roles") or []
    locations = params.get("locations") or master_profile.get("preferred_locations") or []

    query = " ".join(roles[:2]) if roles else None
    location = locations[0] if locations else None

    # Fetch from enabled sources
    raw_jobs, source_reports = source_registry.fetch_all_sources(query=query, location=location)

    # Normalization
    normalized_jobs = []
    for raw in raw_jobs:
        try:
            norm = normalize_job_dict(raw)
            normalized_jobs.append(norm)
        except Exception:
            continue

    # Deduplication and Expiration checks
    deduped_jobs, dup_count = detect_and_link_duplicates(normalized_jobs)
    processed_jobs, exp_count = apply_expiration_check(deduped_jobs, max_expiry_days=Config.JOB_EXPIRY_DAYS)

    # Upsert into MongoDB jobs collection
    stored_count = 0
    now = datetime.now(timezone.utc)

    for job in processed_jobs:
        job["last_checked_at"] = now
        jobs_col.update_one(
            {"job_id": job["job_id"]},
            {
                "$set": job,
                "$setOnInsert": {"first_seen_at": job.get("first_seen_at", now)}
            },
            upsert=True
        )
        stored_count += 1

    return {
        "fetched": len(raw_jobs),
        "stored": stored_count,
        "duplicates_flagged": dup_count,
        "expired_flagged": exp_count,
        "sources_queried": source_reports
    }


def get_jobs_feed(user_id: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieves a paginated, filterable feed of job postings.
    Attaches is_saved indicator for the requesting user.
    """
    jobs_col = get_jobs_collection()
    saved_col = get_saved_jobs_collection()

    page = max(1, int(query_params.get("page", 1)))
    limit = min(50, max(1, int(query_params.get("limit", 12))))
    skip = (page - 1) * limit

    mongo_filter: Dict[str, Any] = {}

    # 1. Exclude expired by default
    exclude_expired = str(query_params.get("exclude_expired", "true")).lower() in ("true", "1", "yes")
    if exclude_expired:
        mongo_filter["status"] = "active"

    # 2. Exclude secondary duplicates from main feed if requested (default True)
    hide_duplicates = str(query_params.get("hide_duplicates", "true")).lower() in ("true", "1", "yes")
    if hide_duplicates:
        mongo_filter["duplicate_group_id"] = None

    # 3. Fresher Only filter
    fresher_only = str(query_params.get("fresher_only", "false")).lower() in ("true", "1", "yes")
    if fresher_only:
        mongo_filter["fresher_status"] = {"$in": ["fresher_friendly", "entry_level"]}
    elif query_params.get("fresher_status"):
        mongo_filter["fresher_status"] = query_params["fresher_status"]

    # 4. Work mode
    work_mode = query_params.get("work_mode")
    if work_mode and work_mode != "all":
        mongo_filter["work_mode"] = work_mode

    # 5. Job type
    job_type = query_params.get("job_type")
    if job_type and job_type != "all":
        mongo_filter["job_type"] = job_type

    # 6. Source
    source = query_params.get("source")
    if source and source != "all":
        mongo_filter["source"] = source

    # 7. Role / Search keyword
    search_term = query_params.get("search") or query_params.get("role")
    if search_term:
        regex = {"$regex": search_term.strip(), "$options": "i"}
        mongo_filter["$or"] = [
            {"title": regex},
            {"company": regex},
            {"location": regex},
            {"required_skills": regex}
        ]

    # 8. Location filter
    loc = query_params.get("location")
    if loc:
        mongo_filter["location"] = {"$regex": loc.strip(), "$options": "i"}

    # Total count
    total = jobs_col.count_documents(mongo_filter)
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Fetch jobs sorted by posted_at descending
    cursor = jobs_col.find(mongo_filter).sort("posted_at", -1).skip(skip).limit(limit)
    job_docs = list(cursor)

    # Fetch candidate's saved job IDs to attach is_saved
    saved_cursor = saved_col.find({"user_id": str(user_id)})
    saved_job_ids = {doc["job_id"] for doc in saved_cursor}

    # Fetch candidate's computed matches for these jobs (Module 5 integration)
    job_ids = [doc["job_id"] for doc in job_docs]
    user_matches: Dict[str, Any] = {}
    try:
        from backend.database import get_job_matches_collection
        from bson import ObjectId
        matches_col = get_job_matches_collection()
        user_oid = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id
        matches_cursor = matches_col.find({
            "$or": [{"user_id": user_oid}, {"user_id": str(user_id)}],
            "job_id": {"$in": job_ids}
        })
        for m in matches_cursor:
            user_matches[m["job_id"]] = {
                "category": m.get("category"),
                "skill_coverage": m.get("skill_coverage")
            }
    except Exception:
        pass

    serialized_jobs = []
    for doc in job_docs:
        s_job = serialize_job(doc, is_saved=(doc["job_id"] in saved_job_ids))
        if doc["job_id"] in user_matches:
            s_job["match"] = user_matches[doc["job_id"]]
        else:
            s_job["match"] = None
        serialized_jobs.append(s_job)

    # Fresher friendly count
    fresher_count = jobs_col.count_documents({
        "status": "active",
        "duplicate_group_id": None,
        "fresher_status": {"$in": ["fresher_friendly", "entry_level"]}
    })

    return {
        "jobs": serialized_jobs,
        "total": total,
        "page": page,
        "pages": total_pages,
        "limit": limit,
        "fresher_friendly_count": fresher_count
    }


def get_job_by_id(user_id: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves single job document by job_id hash or ObjectId."""
    jobs_col = get_jobs_collection()
    saved_col = get_saved_jobs_collection()

    job_doc = jobs_col.find_one({"job_id": str(job_id)})
    if not job_doc:
        try:
            job_doc = jobs_col.find_one({"_id": ObjectId(job_id)})
        except Exception:
            job_doc = None

    if not job_doc:
        return None

    is_saved = bool(saved_col.find_one({"user_id": str(user_id), "job_id": job_doc["job_id"]}))
    return serialize_job(job_doc, is_saved=is_saved)


def save_job(user_id: str, job_id: str, notes: str = "") -> Dict[str, Any]:
    """Saves/bookmarks a job posting for the authenticated candidate."""
    jobs_col = get_jobs_collection()
    saved_col = get_saved_jobs_collection()

    job = jobs_col.find_one({"job_id": str(job_id)})
    if not job:
        raise ValueError("Job posting not found.")

    now = datetime.now(timezone.utc)
    saved_col.update_one(
        {"user_id": str(user_id), "job_id": str(job_id)},
        {
            "$set": {
                "user_id": str(user_id),
                "job_id": str(job_id),
                "saved_at": now,
                "notes": (notes or "").strip()[:500]
            }
        },
        upsert=True
    )

    return {"status": "success", "message": "Job successfully saved to your list."}


def unsave_job(user_id: str, job_id: str) -> bool:
    """Removes a job posting from the candidate's saved list."""
    saved_col = get_saved_jobs_collection()
    res = saved_col.delete_one({"user_id": str(user_id), "job_id": str(job_id)})
    return res.deleted_count > 0


def get_saved_jobs(user_id: str) -> List[Dict[str, Any]]:
    """Retrieves all jobs saved by the user with notes and save timestamps."""
    jobs_col = get_jobs_collection()
    saved_col = get_saved_jobs_collection()

    saved_cursor = saved_col.find({"user_id": str(user_id)}).sort("saved_at", -1)
    saved_entries = list(saved_cursor)

    results: List[Dict[str, Any]] = []
    for entry in saved_entries:
        job_doc = jobs_col.find_one({"job_id": entry["job_id"]})
        if job_doc:
            s_job = serialize_job(job_doc, is_saved=True)
            s_job["saved_at"] = entry["saved_at"].isoformat() if isinstance(entry["saved_at"], datetime) else None
            s_job["saved_notes"] = entry.get("notes", "")
            results.append(s_job)

    return results


def update_discovery_preferences(user_id: str, prefs_data: Dict[str, Any]) -> Dict[str, Any]:
    """Updates candidate discovery preferences on the candidate_profiles document."""
    profiles_col = get_profiles_collection()

    set_dict = {
        "discovery_preferences": {
            "work_mode": prefs_data.get("work_mode", ["remote", "hybrid", "onsite"]),
            "job_type": prefs_data.get("job_type", ["full_time", "internship"]),
            "industries": prefs_data.get("industries", []),
            "fresher_only": bool(prefs_data.get("fresher_only", True))
        },
        "updated_at": datetime.now(timezone.utc)
    }

    if "preferred_roles" in prefs_data and isinstance(prefs_data["preferred_roles"], list):
        set_dict["preferred_roles"] = [r.strip() for r in prefs_data["preferred_roles"] if isinstance(r, str) and r.strip()]

    if "preferred_locations" in prefs_data and isinstance(prefs_data["preferred_locations"], list):
        set_dict["preferred_locations"] = [l.strip() for l in prefs_data["preferred_locations"] if isinstance(l, str) and l.strip()]

    profiles_col.update_one({"user_id": str(user_id)}, {"$set": set_dict}, upsert=True)
    return set_dict["discovery_preferences"]

