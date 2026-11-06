"""
Sample Job Source Adapter.
Loads verified realistic fake fresher listings from backend/data/sample_jobs.json.
All jobs are strictly tagged is_sample=True with placeholder application URLs.
"""

import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path

from backend.config import Config
from backend.services.job_sources.base import JobSource


SAMPLE_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sample_jobs.json"


class SampleJobSource(JobSource):
    """Curated sample jobs source for offline testing and fresher exploration."""

    def __init__(self):
        super().__init__(name="sample", timeout_seconds=2, cache_ttl_seconds=60)

    @property
    def is_enabled(self) -> bool:
        return Config.ENABLE_SAMPLE_SOURCE and os.path.exists(SAMPLE_DATA_PATH)

    def fetch_raw_jobs(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        if not os.path.exists(SAMPLE_DATA_PATH):
            return []

        with open(SAMPLE_DATA_PATH, "r", encoding="utf-8") as f:
            raw_items = json.load(f)

        now = datetime.now(timezone.utc)
        normalized_query = (query or "").strip().lower()
        normalized_loc = (location or "").strip().lower()

        jobs: List[Dict[str, Any]] = []

        for item in raw_items:
            # Query match check
            if normalized_query:
                title_match = normalized_query in item.get("title", "").lower()
                desc_match = normalized_query in item.get("description", "").lower()
                skills_match = any(normalized_query in s.lower() for s in item.get("required_skills", []))
                if not (title_match or desc_match or skills_match):
                    continue

            # Location match check
            if normalized_loc:
                item_loc = item.get("location", "").lower()
                item_work = item.get("work_mode", "").lower()
                if normalized_loc not in item_loc and normalized_loc not in item_work:
                    continue

            # Dynamic date calculations
            posted_days = item.get("posted_days_ago", 1)
            posted_at = now - timedelta(days=posted_days)

            deadline_days = item.get("deadline_days_ahead")
            deadline = (now + timedelta(days=deadline_days)) if deadline_days is not None else None

            # Generate stable deterministic job_id hash
            raw_id = item.get("id", "sample_default")
            job_id_hash = hashlib.sha256(f"sample_{raw_id}".encode()).hexdigest()[:16]

            job_dict = {
                "job_id": job_id_hash,
                "title": item.get("title", ""),
                "company": item.get("company", ""),
                "location": item.get("location", "Remote"),
                "work_mode": item.get("work_mode", "unknown"),
                "job_type": item.get("job_type", "full_time"),
                "experience_text": item.get("experience_text", ""),
                "education_required": item.get("education_required", ""),
                "required_skills": item.get("required_skills", []),
                "description": item.get("description", ""),
                "salary_text": item.get("salary_text"),
                "application_url": f"https://example.com/sample-job/{raw_id}",
                "source": "sample",
                "is_sample": True,
                "posted_at": posted_at,
                "deadline": deadline,
                "first_seen_at": posted_at,
                "last_checked_at": now
            }
            jobs.append(job_dict)
            if len(jobs) >= limit:
                break

        return jobs

