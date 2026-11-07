"""
Job Models and Serialization for CareerPilot AI (Module 4).
Defines schemas for normalized job postings, discovery preferences, and saved jobs.
"""

from datetime import datetime, timezone
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator, AnyHttpUrl


WorkModeType = Literal["remote", "onsite", "hybrid", "unknown"]
JobTypeType = Literal["full_time", "internship", "contract", "unknown"]
FresherStatusType = Literal["fresher_friendly", "entry_level", "experience_required", "unclear"]
JobStatusType = Literal["active", "expired", "unknown"]


class JobSchema(BaseModel):
    job_id: str = Field(..., min_length=4, max_length=128)
    title: str = Field(..., min_length=2, max_length=200)
    normalized_title: str = Field(..., min_length=2, max_length=200)
    company: str = Field(..., min_length=1, max_length=150)
    location: str = Field(default="Remote", max_length=150)
    work_mode: WorkModeType = "unknown"
    job_type: JobTypeType = "full_time"
    experience_text: str = Field(default="", max_length=200)
    experience_min_years: Optional[float] = Field(default=None, ge=0, le=50)
    experience_max_years: Optional[float] = Field(default=None, ge=0, le=50)
    fresher_status: FresherStatusType = "unclear"
    education_required: str = Field(default="", max_length=250)
    required_skills: List[str] = Field(default_factory=list)
    description: str = Field(default="", max_length=5000)
    salary_text: Optional[str] = Field(default=None, max_length=150)
    application_url: str = Field(..., max_length=500)
    source: str = Field(..., max_length=50)
    is_sample: bool = False
    is_test_scenario: bool = False
    recruiter_name: Optional[str] = Field(default=None, max_length=120)
    recruiter_email: Optional[str] = Field(default=None, max_length=150)
    posted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deadline: Optional[datetime] = None
    status: JobStatusType = "active"
    first_seen_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duplicate_group_id: Optional[str] = None

    @field_validator("application_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        s = v.strip()
        if not (s.startswith("http://") or s.startswith("https://")):
            raise ValueError("application_url must begin with http:// or https://")
        return s

    @field_validator("required_skills")
    @classmethod
    def clean_skills(cls, v: List[str]) -> List[str]:
        cleaned = []
        for item in v:
            if isinstance(item, str) and item.strip():
                s = item.strip()
                if s not in cleaned:
                    cleaned.append(s[:50])
        return cleaned


class DiscoveryPreferencesSchema(BaseModel):
    work_mode: List[WorkModeType] = Field(default_factory=lambda: ["remote", "hybrid", "onsite"])
    job_type: List[JobTypeType] = Field(default_factory=lambda: ["full_time", "internship"])
    industries: List[str] = Field(default_factory=list)
    fresher_only: bool = True
    preferred_roles: List[str] = Field(default_factory=list)
    preferred_locations: List[str] = Field(default_factory=list)

    @field_validator("industries", "preferred_roles", "preferred_locations")
    @classmethod
    def clean_list(cls, v: List[str]) -> List[str]:
        return [i.strip()[:100] for i in v if isinstance(i, str) and i.strip()]


class JobDiscoverRequestSchema(BaseModel):
    roles: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    work_mode: Optional[WorkModeType] = None
    job_type: Optional[JobTypeType] = None
    fresher_only: Optional[bool] = None


class SaveJobRequestSchema(BaseModel):
    notes: Optional[str] = Field(default="", max_length=500)


def serialize_job(job_doc: Dict[str, Any], is_saved: bool = False) -> Dict[str, Any]:
    """Serializes a MongoDB job document into a clean API response dict."""
    if not job_doc:
        return {}

    doc = dict(job_doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))

    for date_key in ["posted_at", "deadline", "first_seen_at", "last_checked_at"]:
        val = doc.get(date_key)
        if isinstance(val, datetime):
            doc[date_key] = val.isoformat()

    doc["is_saved"] = is_saved
    return doc

