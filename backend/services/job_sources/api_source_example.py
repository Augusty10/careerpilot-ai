"""
Adzuna API Job Source Adapter.
Official job search API adapter with free tier support.
Respects rate limits, timeouts, and is disabled gracefully when credentials are not set.
"""

import urllib.request
import urllib.parse
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging

from backend.config import Config
from backend.services.job_sources.base import JobSource

logger = logging.getLogger(__name__)


class AdzunaJobSource(JobSource):
    """
    Official Adzuna Job Search API Adapter.
    Configured via ADZUNA_APP_ID and ADZUNA_APP_KEY in .env.
    """

    def __init__(self):
        super().__init__(name="adzuna_api", timeout_seconds=8, cache_ttl_seconds=300)

    @property
    def is_enabled(self) -> bool:
        """Only enabled if valid non-empty credentials are configured."""
        return bool(Config.ADZUNA_APP_ID and Config.ADZUNA_APP_KEY)

    def fetch_raw_jobs(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        if not self.is_enabled:
            return []

        country = Config.ADZUNA_COUNTRY or "in"
        base_url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"

        params = {
            "app_id": Config.ADZUNA_APP_ID,
            "app_key": Config.ADZUNA_APP_KEY,
            "results_per_page": min(limit, 50),
            "content-type": "application/json"
        }

        if query:
            params["what"] = query.strip()
        if location:
            params["where"] = location.strip()

        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "CareerPilot-AI-Fresher-Discovery/1.0",
                "Accept": "application/json"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                if resp.status != 200:
                    logger.warning(f"[AdzunaJobSource] API returned HTTP status {resp.status}")
                    return []
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.warning(f"[AdzunaJobSource] Failed to reach Adzuna API: {e}")
            return []

        raw_results = payload.get("results", [])
        jobs: List[Dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        for item in raw_results:
            source_id = str(item.get("id", ""))
            job_id_hash = hashlib.sha256(f"adzuna_{source_id}".encode()).hexdigest()[:16]

            # Parse created date
            posted_at = now
            created_str = item.get("created")
            if created_str:
                try:
                    posted_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                except Exception:
                    posted_at = now

            salary_min = item.get("salary_min")
            salary_max = item.get("salary_max")
            salary_text = None
            if salary_min or salary_max:
                salary_text = f"₹{int(salary_min or 0):,} - ₹{int(salary_max or 0):,} P.A."

            company_data = item.get("company", {})
            company_name = company_data.get("display_name", "Technology Employer")

            location_data = item.get("location", {})
            loc_display = location_data.get("display_name", "India")

            app_url = item.get("redirect_url", f"https://example.com/job/{source_id}")

            jobs.append({
                "job_id": job_id_hash,
                "title": item.get("title", "Software Developer"),
                "company": company_name,
                "location": loc_display,
                "work_mode": "remote" if "remote" in loc_display.lower() else "unknown",
                "job_type": "full_time" if item.get("contract_time") == "full_time" else "unknown",
                "experience_text": "",
                "education_required": "",
                "required_skills": [],
                "description": item.get("description", ""),
                "salary_text": salary_text,
                "application_url": app_url,
                "source": "adzuna_api",
                "is_sample": False,
                "posted_at": posted_at,
                "deadline": None,
                "first_seen_at": now,
                "last_checked_at": now
            })

        return jobs

