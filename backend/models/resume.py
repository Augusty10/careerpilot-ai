from datetime import datetime, timezone
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ResumePersonalSchema(BaseModel):
    full_name: str = Field(default="", max_length=150)
    email: str = Field(default="", max_length=150)
    phone: str = Field(default="", max_length=30)
    location: str = Field(default="", max_length=150)
    linkedin_url: Optional[str] = Field(default=None, max_length=250)
    github_url: Optional[str] = Field(default=None, max_length=250)


class ResumeSkillCategorySchema(BaseModel):
    category: str = Field(..., max_length=50)
    items: List[str] = Field(default_factory=list)

    @field_validator("items")
    @classmethod
    def clean_items(cls, v: List[str]) -> List[str]:
        return [i.strip() for i in v if isinstance(i, str) and i.strip()]


class ResumeProjectSchema(BaseModel):
    source_index: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=150)
    description_bullets: List[str] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)
    link: Optional[str] = Field(default=None, max_length=250)

    @field_validator("description_bullets")
    @classmethod
    def clean_bullets(cls, v: List[str]) -> List[str]:
        return [b.strip() for b in v if isinstance(b, str) and b.strip()]


class ResumeInternshipSchema(BaseModel):
    source_index: Optional[int] = None
    company: str = Field(..., min_length=1, max_length=150)
    role: str = Field(..., min_length=1, max_length=150)
    start_date: Optional[str] = Field(default="", max_length=50)
    end_date: Optional[str] = Field(default="", max_length=50)
    description_bullets: List[str] = Field(default_factory=list)


class ResumeWorkExperienceSchema(BaseModel):
    source_index: Optional[int] = None
    company: str = Field(..., min_length=1, max_length=150)
    role: str = Field(..., min_length=1, max_length=150)
    start_date: Optional[str] = Field(default="", max_length=50)
    end_date: Optional[str] = Field(default="", max_length=50)
    description_bullets: List[str] = Field(default_factory=list)


class ResumeEducationSchema(BaseModel):
    degree: str = Field(..., min_length=1, max_length=150)
    institution: str = Field(..., min_length=1, max_length=200)
    graduation_year: Optional[int] = Field(default=None)
    score_type: Optional[str] = Field(default="cgpa")
    score: Optional[float] = Field(default=None)


class ResumeCertificationSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    issuer: Optional[str] = Field(default="", max_length=150)
    year: Optional[int] = Field(default=None)


class ResumeContentSchema(BaseModel):
    personal: ResumePersonalSchema = Field(default_factory=ResumePersonalSchema)
    summary: str = Field(default="", max_length=1500)
    skills: List[ResumeSkillCategorySchema] = Field(default_factory=list)
    projects: List[ResumeProjectSchema] = Field(default_factory=list)
    internships: List[ResumeInternshipSchema] = Field(default_factory=list)
    work_experience: List[ResumeWorkExperienceSchema] = Field(default_factory=list)
    education: List[ResumeEducationSchema] = Field(default_factory=list)
    certifications: List[ResumeCertificationSchema] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)


class ResumeGenerateRequestSchema(BaseModel):
    target_role: str = Field(..., min_length=2, max_length=100)
    template: Optional[Literal["classic", "modern"]] = "modern"
    resume_name: Optional[str] = Field(default=None, max_length=150)


class ResumeGenerateMultipleRequestSchema(BaseModel):
    target_roles: List[str] = Field(..., min_length=1, max_length=5)
    template: Optional[Literal["classic", "modern"]] = "modern"

    @field_validator("target_roles")
    @classmethod
    def clean_roles(cls, v: List[str]) -> List[str]:
        cleaned = [r.strip() for r in v if isinstance(r, str) and r.strip()]
        if not cleaned:
            raise ValueError("At least one target role is required")
        if len(cleaned) > 5:
            raise ValueError("Maximum 5 target roles can be generated at once")
        return cleaned


class ResumeUpdateRequestSchema(BaseModel):
    resume_name: Optional[str] = Field(default=None, max_length=150)
    template: Optional[Literal["classic", "modern"]] = None
    content: ResumeContentSchema


class ResumeCustomizeRequestSchema(BaseModel):
    job_id: str = Field(..., min_length=4, max_length=128)
    base_resume_id: Optional[str] = None
    template: Optional[Literal["classic", "modern"]] = "modern"
    resume_name: Optional[str] = Field(default=None, max_length=150)


def serialize_resume(resume_doc: Dict[str, Any], master_profile_updated_at: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Serializes a MongoDB resume document into an API response dictionary.
    Computes whether the resume is 'is_outdated' based on profile update timestamp.
    """
    if not resume_doc:
        return {}

    doc = dict(resume_doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))

    created_at = doc.get("created_at")
    if isinstance(created_at, datetime):
        doc["created_at"] = created_at.isoformat()

    updated_at = doc.get("updated_at")
    if isinstance(updated_at, datetime):
        doc["updated_at"] = updated_at.isoformat()

    approved_at = doc.get("approved_at")
    if isinstance(approved_at, datetime):
        doc["approved_at"] = approved_at.isoformat()

    gen_profile_time = doc.get("generated_from_profile_updated_at")
    if isinstance(gen_profile_time, datetime):
        doc["generated_from_profile_updated_at"] = gen_profile_time.isoformat()

    # Outdated check
    is_outdated = False
    if master_profile_updated_at and gen_profile_time:
        if isinstance(gen_profile_time, str):
            try:
                gen_profile_time = datetime.fromisoformat(gen_profile_time)
            except Exception:
                pass
        if isinstance(master_profile_updated_at, str):
            try:
                master_profile_updated_at = datetime.fromisoformat(master_profile_updated_at)
            except Exception:
                pass
        if isinstance(master_profile_updated_at, datetime) and isinstance(gen_profile_time, datetime):
            # Normalise timezone for comparison
            p_time = master_profile_updated_at if master_profile_updated_at.tzinfo else master_profile_updated_at.replace(tzinfo=timezone.utc)
            g_time = gen_profile_time if gen_profile_time.tzinfo else gen_profile_time.replace(tzinfo=timezone.utc)
            is_outdated = p_time > g_time

    doc["is_outdated"] = is_outdated
    return doc

