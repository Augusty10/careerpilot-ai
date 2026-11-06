from datetime import datetime, timezone
from typing import List, Optional, Literal, Dict, Any, Union
from pydantic import BaseModel, Field


MatchCategory = Literal["strong_match", "partial_match", "low_match", "not_eligible"]


class RelatedSkillItem(BaseModel):
    job_skill: str
    candidate_skill: str
    relationship: Optional[str] = None


class SkillsMatchBreakdown(BaseModel):
    matched: List[str] = Field(default_factory=list)
    related: List[RelatedSkillItem] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    total_required: int = 0
    raw_job_skills: List[str] = Field(default_factory=list)


class RequirementStatusItem(BaseModel):
    status: str
    job_requirement: Optional[str] = None
    candidate_value: Optional[Union[str, int, float, List[str], Dict[str, Any]]] = None
    details: Optional[str] = None


class CertificationsMatchItem(BaseModel):
    status: str
    missing: List[str] = Field(default_factory=list)
    job_requirement: Optional[str] = None


class JobMatchSchema(BaseModel):
    user_id: str
    job_id: str
    profile_version_hash: str
    category: MatchCategory
    skill_coverage: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    skills: SkillsMatchBreakdown
    education: RequirementStatusItem
    graduation_year: RequirementStatusItem
    experience: RequirementStatusItem
    location: RequirementStatusItem
    job_type: RequirementStatusItem
    certifications: CertificationsMatchItem
    hard_failures: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    explanation: str = Field(default="")
    explanation_source: Literal["rules", "ai"] = "rules"
    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BatchMatchRequestSchema(BaseModel):
    job_ids: List[str] = Field(..., min_length=1, max_length=50)


def serialize_match(doc: Dict[str, Any], is_stale: bool = False) -> Dict[str, Any]:
    """Serializes a job_matches MongoDB document into a clean JSON-serializable dict."""
    if not doc:
        return {}

    match_id = str(doc.get("_id")) if doc.get("_id") else None
    user_id = str(doc.get("user_id")) if doc.get("user_id") else None

    computed_at = doc.get("computed_at")
    if isinstance(computed_at, datetime):
        computed_at_str = computed_at.isoformat()
    else:
        computed_at_str = str(computed_at) if computed_at else None

    # Handle nested fields safely
    skills = doc.get("skills", {})
    if isinstance(skills, dict):
        skills_clean = {
            "matched": skills.get("matched", []),
            "related": skills.get("related", []),
            "missing": skills.get("missing", []),
            "total_required": skills.get("total_required", 0),
            "raw_job_skills": skills.get("raw_job_skills", [])
        }
    else:
        skills_clean = {"matched": [], "related": [], "missing": [], "total_required": 0, "raw_job_skills": []}

    return {
        "id": match_id,
        "user_id": user_id,
        "job_id": doc.get("job_id"),
        "profile_version_hash": doc.get("profile_version_hash"),
        "category": doc.get("category"),
        "skill_coverage": doc.get("skill_coverage"),
        "skills": skills_clean,
        "education": doc.get("education", {}),
        "graduation_year": doc.get("graduation_year", {}),
        "experience": doc.get("experience", {}),
        "location": doc.get("location", {}),
        "job_type": doc.get("job_type", {}),
        "certifications": doc.get("certifications", {}),
        "hard_failures": doc.get("hard_failures", []),
        "warnings": doc.get("warnings", []),
        "explanation": doc.get("explanation", ""),
        "explanation_source": doc.get("explanation_source", "rules"),
        "computed_at": computed_at_str,
        "is_stale": is_stale,
        "disclaimer": "This reflects how many required skills you have. It is not a prediction of being hired."
    }

