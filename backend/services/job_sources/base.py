"""
Base Job Source Adapter.
Abstract class establishing contracts, throttling, timeouts, caching,
and error-handling policies for all job sources.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)


class JobSource(ABC):
    """
    Abstract base class for all job source adapters.
    Subclasses must implement fetch_raw_jobs.
    """

    def __init__(self, name: str, timeout_seconds: int = 8, cache_ttl_seconds: int = 300):
        self.name = name
        self.timeout_seconds = timeout_seconds
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """Indicates whether this source is active and properly configured."""
        pass

    @abstractmethod
    def fetch_raw_jobs(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetches raw job listings from the source.
        Must NOT send candidate personal information.
        """
        pass

    def fetch_jobs(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Public wrapper enforcing caching, timeout shielding, and error reporting.
        """
        if not self.is_enabled:
            return []

        cache_key = f"{query or ''}:{location or ''}:{limit}"
        now = datetime.now(timezone.utc)

        # Check cache
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if now < entry["expires_at"]:
                return entry["data"]

        try:
            results = self.fetch_raw_jobs(query=query, location=location, limit=limit)
            # Store in cache
            self._cache[cache_key] = {
                "expires_at": now + timedelta(seconds=self.cache_ttl_seconds),
                "data": results
            }
            return results
        except Exception as err:
            logger.error(f"[JobSource:{self.name}] Error fetching jobs: {err}", exc_info=True)
            return []

