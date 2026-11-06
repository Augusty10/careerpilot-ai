from datetime import datetime, timezone
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class PersonalDetailsSchema(BaseModel):
    full_name: str = Field(default="", max_length=150)
    email: str = Field(default="", max_length=150)
    phone: str = Field(default="", max_length=30)
    location: str = Field(default="", max_length=150)
    linkedin_url: Optional[str] = Field(default=None, max_length=250)
    github_url: Optional[str] = Field(default=None, max_length=250)

    @field_validator("email")
    @classmethod
    def clean_email(cls, v: str) -> str:
        return v.strip().lower() if v else ""

    @field_validator("full_name", "phone", "location")
    @classmethod
    def clean_text(cls, v: str) -> str:
        return v.strip() if v else ""


class EducationItemSchema(BaseModel):
    degree: str = Field(..., min_length=1, max_length=150)
    institution: str = Field(..., min_length=1, max_length=200)
    graduation_year: Optional[int] = Field(default=None, ge=1970, le=2040)
    score_type: Optional[Literal["cgpa", "percentage"]] = "cgpa"
    score: Optional[float] = Field(default=None)

    @model_validator(mode="after")
    def validate_score(self):
        if self.score is not None:
            if self.score_type == "cgpa":
                if not (0.0 <= self.score <= 10.0):
                    raise ValueError("CGPA must be between 0.0 and 10.0")
            elif self.score_type == "percentage":
                if not (0.0 <= self.score <= 100.0):
                    raise ValueError("Percentage must be between 0.0 and 100.0")
        return self


class SkillsSchema(BaseModel):
    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    other: List[str] = Field(default_factory=list)

    @field_validator("languages", "frameworks", "databases", "tools", "other")
    @classmethod
    def clean_tags(cls, tags: List[str]) -> List[str]:
        cleaned = []
        for t in tags:
            if isinstance(t, str):
                s = t.strip()
                if s and s not in cleaned:
                    cleaned.append(s[:50])
        return cleaned


class ProjectItemSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: str = Field(default="", max_length=2000)
    tech_stack: List[str] = Field(default_factory=list)
    link: Optional[str] = Field(default=None, max_length=250)

    @field_validator("tech_stack")
    @classmethod
    def clean_tech_stack(cls, tags: List[str]) -> List[str]:
        return [t.strip()[:50] for t in tags if isinstance(t, str) and t.strip()]


class InternshipItemSchema(BaseModel):
    company: str = Field(..., min_length=1, max_length=150)
    role: str = Field(..., min_length=1, max_length=150)
    start_date: Optional[str] = Field(default="", max_length=50)
    end_date: Optional[str] = Field(default="", max_length=50)
    description: Optional[str] = Field(default="", max_length=2000)


class CertificationItemSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    issuer: str = Field(default="", max_length=150)
    year: Optional[int] = Field(default=None, ge=1970, le=2040)


class WorkExperienceItemSchema(BaseModel):
    company: str = Field(..., min_length=1, max_length=150)
    role: str = Field(..., min_length=1, max_length=150)
    start_date: Optional[str] = Field(default="", max_length=50)
    end_date: Optional[str] = Field(default="", max_length=50)
    description: Optional[str] = Field(default="", max_length=2000)


class CandidateProfileSchema(BaseModel):
    personal: PersonalDetailsSchema = Field(default_factory=PersonalDetailsSchema)
    education: List[EducationItemSchema] = Field(default_factory=list)
    skills: SkillsSchema = Field(default_factory=SkillsSchema)
    projects: List[ProjectItemSchema] = Field(default_factory=list)
    internships: List[InternshipItemSchema] = Field(default_factory=list)
    certifications: List[CertificationItemSchema] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    work_experience: List[WorkExperienceItemSchema] = Field(default_factory=list)
    preferred_roles: List[str] = Field(default_factory=list)
    preferred_locations: List[str] = Field(default_factory=list)
    profile_status: Literal["draft", "approved"] = "draft"

    @field_validator("achievements", "preferred_roles", "preferred_locations")
    @classmethod
    def clean_string_list(cls, items: List[str]) -> List[str]:
        return [i.strip()[:200] for i in items if isinstance(i, str) and i.strip()]


def get_empty_profile_skeleton(user_id: str, full_name: str = "", email: str = "") -> Dict[str, Any]:
    """Generates a default empty skeleton for a candidate profile."""
    now = datetime.now(timezone.utc)
    return {
      "user_id": str(user_id),
      "personal": {
        "full_name": full_name or "",
        "email": email or "",
        "phone": "",
        "location": "",
        "linkedin_url": "",
        "github_url": ""
      },
      "education": [],
      "skills": {
        "languages": [],
        "frameworks": [],
        "databases": [],
        "tools": [],
        "other": []
      },
      "projects": [],
      "internships": [],
      "certifications": [],
      "achievements": [],
      "work_experience": [],
      "preferred_roles": [],
      "preferred_locations": [],
      "profile_status": "draft",
      "completeness": 15 if full_name and email else 0,
      "created_at": now.isoformat(),
      "updated_at": now.isoformat(),
    }


def calculate_profile_completeness(profile: Dict[str, Any]) -> int:
    """Calculates profile completeness percentage (0 to 100)."""
    score = 0
    total = 100

    personal = profile.get("personal", {})
    if personal.get("full_name"):
        score += 5
    if personal.get("email"):
        score += 5
    if personal.get("phone"):
        score += 5
    if personal.get("location"):
        score += 5
    if personal.get("linkedin_url") or personal.get("github_url"):
        score += 5

    education = profile.get("education", [])
    if education and len(education) > 0:
        score += 20

    skills = profile.get("skills", {})
    skill_count = sum(len(skills.get(cat, [])) for cat in ["languages", "frameworks", "databases", "tools", "other"])
    if skill_count >= 5:
        score += 20
    elif skill_count > 0:
        score += 10

    projects = profile.get("projects", [])
    if projects and len(projects) > 0:
        score += 15

    internships = profile.get("internships", [])
    work_exp = profile.get("work_experience", [])
    if len(internships) > 0 or len(work_exp) > 0:
        score += 10

    certs = profile.get("certifications", [])
    achievements = profile.get("achievements", [])
    if len(certs) > 0 or len(achievements) > 0:
        score += 5

    roles = profile.get("preferred_roles", [])
    if roles and len(roles) > 0:
        score += 5

    return min(total, score)


def serialize_profile(profile_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Serializes a MongoDB profile document into a clean API response."""
    if not profile_doc:
        return {}

    doc = dict(profile_doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))

    created_at = doc.get("created_at")
    if isinstance(created_at, datetime):
        doc["created_at"] = created_at.isoformat()

    updated_at = doc.get("updated_at")
    if isinstance(updated_at, datetime):
        doc["updated_at"] = updated_at.isoformat()

    doc["completeness"] = calculate_profile_completeness(doc)
    return doc

