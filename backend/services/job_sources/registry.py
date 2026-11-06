"""
Job Source Registry.
Manages discovered and enabled job sources and provides unified query dispatcher.
"""

from typing import List, Dict, Any, Optional, Tuple
import concurrent.futures

from backend.services.job_sources.base import JobSource
from backend.services.job_sources.sample_source import SampleJobSource
from backend.services.job_sources.api_source_example import AdzunaJobSource


class JobSourceRegistry:
    """Central registry of all configured job source adapters."""

    def __init__(self):
        self._sources: List[JobSource] = [
            SampleJobSource(),
            AdzunaJobSource(),
        ]

    def get_sources_info(self) -> List[Dict[str, Any]]:
        """Returns metadata regarding configured sources and their activation status."""
        return [
            {
                "name": src.name,
                "is_enabled": src.is_enabled,
                "type": "sample_seed" if src.name == "sample" else "official_api"
            }
            for src in self._sources
        ]

    def get_enabled_sources(self) -> List[JobSource]:
        """Returns list of currently active, enabled sources."""
        return [src for src in self._sources if src.is_enabled]

    def fetch_all_sources(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        limit_per_source: int = 50
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Executes parallel fetch across all enabled sources with error isolation.
        Returns: (all_raw_jobs, source_status_reports)
        """
        enabled = self.get_enabled_sources()
        all_jobs: List[Dict[str, Any]] = []
        reports: List[Dict[str, Any]] = []

        if not enabled:
            return [], [{"error": "No job sources are currently enabled"}]

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(enabled)) as executor:
            future_to_src = {
                executor.submit(src.fetch_jobs, query, location, limit_per_source): src
                for src in enabled
            }

            for future in concurrent.futures.as_completed(future_to_src):
                src = future_to_src[future]
                try:
                    jobs = future.result()
                    all_jobs.extend(jobs)
                    reports.append({
                        "source": src.name,
                        "status": "success",
                        "count": len(jobs)
                    })
                except Exception as err:
                    reports.append({
                        "source": src.name,
                        "status": "error",
                        "error": str(err),
                        "count": 0
                    })

        return all_jobs, reports


# Singleton instance
source_registry = JobSourceRegistry()

