"""
Job Deduplication and Expiration Service.
Uses title + company + location fuzzy matching via difflib.SequenceMatcher
to detect duplicate postings and links them via duplicate_group_id.
Detects expired listings based on passed deadlines or configurable staleness days.
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher


def are_jobs_duplicate(job_a: Dict[str, Any], job_b: Dict[str, Any], threshold: float = 0.82) -> bool:
    """
    Determines if two job postings represent the same vacancy.
    Requires matching company, compatible location, and high title similarity.
    """
    comp_a = (job_a.get("company") or "").strip().lower()
    comp_b = (job_b.get("company") or "").strip().lower()

    if not comp_a or comp_a != comp_b:
        return False

    # Location check
    loc_a = (job_a.get("location") or "").strip().lower()
    loc_b = (job_b.get("location") or "").strip().lower()
    is_remote_a = "remote" in loc_a or job_a.get("work_mode") == "remote"
    is_remote_b = "remote" in loc_b or job_b.get("work_mode") == "remote"

    location_matches = (loc_a == loc_b) or (is_remote_a and is_remote_b)
    if not location_matches:
        return False

    # Title similarity
    title_a = (job_a.get("normalized_title") or job_a.get("title") or "").strip().lower()
    title_b = (job_b.get("normalized_title") or job_b.get("title") or "").strip().lower()

    if title_a == title_b:
        return True

    similarity = SequenceMatcher(None, title_a, title_b).ratio()
    if similarity >= threshold:
        return True

    # Word set overlap check for titles with synonyms (e.g. Developer vs Engineer)
    words_a = set(title_a.split())
    words_b = set(title_b.split())
    if words_a and words_b:
        overlap = len(words_a.intersection(words_b)) / max(len(words_a), len(words_b))
        if overlap >= 0.6:
            return True

    return False


def detect_and_link_duplicates(jobs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Identifies duplicate job postings in a batch.
    Sets duplicate_group_id on secondary duplicates linking to the canonical job_id.
    Returns: (processed_jobs, duplicates_count)
    """
    canonical_jobs: List[Dict[str, Any]] = []
    duplicate_count = 0

    for job in jobs:
        if "duplicate_group_id" not in job:
            job["duplicate_group_id"] = None

        # Check against established canonical jobs
        matched_canonical = None
        for canonical in canonical_jobs:
            if are_jobs_duplicate(canonical, job):
                matched_canonical = canonical
                break

        if matched_canonical:
            job["duplicate_group_id"] = matched_canonical.get("job_id")
            duplicate_count += 1
        else:
            canonical_jobs.append(job)

    return jobs, duplicate_count


def is_job_expired(job: Dict[str, Any], max_expiry_days: int = 45) -> bool:
    """
    Checks if a job has expired.
    - True if deadline has passed current time.
    - True if posted_at is older than max_expiry_days.
    """
    now = datetime.now(timezone.utc)

    # 1. Check explicit deadline
    deadline = job.get("deadline")
    if deadline:
        if isinstance(deadline, str):
            try:
                deadline = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
            except Exception:
                deadline = None
        if isinstance(deadline, datetime):
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            if now > deadline:
                return True

    # 2. Check staleness threshold
    posted_at = job.get("posted_at")
    if posted_at:
        if isinstance(posted_at, str):
            try:
                posted_at = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
            except Exception:
                posted_at = None
        if isinstance(posted_at, datetime):
            if posted_at.tzinfo is None:
                posted_at = posted_at.replace(tzinfo=timezone.utc)
            if (now - posted_at) > timedelta(days=max_expiry_days):
                return True

    return False


def apply_expiration_check(jobs: List[Dict[str, Any]], max_expiry_days: int = 45) -> Tuple[List[Dict[str, Any]], int]:
    """
    Evaluates jobs and updates status to 'expired' where applicable.
    Never deletes jobs silently; strictly updates status flag.
    Returns: (processed_jobs, expired_count)
    """
    expired_count = 0
    for job in jobs:
        if is_job_expired(job, max_expiry_days):
            job["status"] = "expired"
            expired_count += 1
        elif job.get("status") not in ["expired", "active"]:
            job["status"] = "active"

    return jobs, expired_count
