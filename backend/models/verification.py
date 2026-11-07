"""
Verification Models and Serialization for CareerPilot AI (Module 6).
Defines schemas for evidence items, warning indicators, multi-entity verification,
recruiter contact submissions, and candidate abuse reports.
"""

from datetime import datetime, timezone
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, EmailStr, field_validator


VerificationStatusType = Literal["corroborated", "needs_verification", "suspicious", "not_applicable"]
CheckResultType = Literal["pass", "fail", "unavailable"]
WarningSeverityType = Literal["low", "medium", "high"]
ReportReasonType = Literal["fee_request", "identity_theft", "unofficial_channel", "fake_company", "other"]


class EvidenceItem(BaseModel):
    check: str = Field(..., max_length=100)
    result: CheckResultType
    detail: str = Field(..., max_length=1000)
    source_url: Optional[str] = Field(default=None, max_length=500)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WarningItem(BaseModel):
    code: str = Field(..., max_length=64)
    severity: WarningSeverityType
    message: str = Field(..., max_length=1000)
    exact_quote: Optional[str] = Field(default=None, max_length=500)


class EntityVerification(BaseModel):
    status: VerificationStatusType = "needs_verification"
    evidence: List[EvidenceItem] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    warnings: List[WarningItem] = Field(default_factory=list)


class RecruiterContact(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    email: Optional[str] = Field(default=None, max_length=150)
    claimed_company: Optional[str] = Field(default=None, max_length=150)


class RecruiterVerification(BaseModel):
    status: VerificationStatusType = "needs_verification"
    provided: bool = False
    contact: RecruiterContact = Field(default_factory=RecruiterContact)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    warnings: List[WarningItem] = Field(default_factory=list)


class JobVerificationSchema(BaseModel):
    job_id: str = Field(..., min_length=4, max_length=128)
    company: EntityVerification = Field(default_factory=EntityVerification)
    recruiter: RecruiterVerification = Field(default_factory=RecruiterVerification)
    job: EntityVerification = Field(default_factory=EntityVerification)
    overall_status: VerificationStatusType = "needs_verification"
    recommended_action: str = Field(..., max_length=1000)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    next_check_after: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    checks_run: List[str] = Field(default_factory=list)
    checks_skipped: List[Dict[str, str]] = Field(default_factory=list)
    verification_history: List[Dict[str, Any]] = Field(default_factory=list)


class SubmitRecruiterDetailsSchema(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    email: str = Field(..., min_length=5, max_length=150)
    claimed_company: Optional[str] = Field(default=None, max_length=150)

    @field_validator("email")
    @classmethod
    def validate_recruiter_email(cls, v: str) -> str:
        s = v.strip().lower()
        if "@" not in s or "." not in s.split("@")[-1]:
            raise ValueError("Invalid email format")
        return s


class UserReportCreateSchema(BaseModel):
    reason: ReportReasonType
    note: str = Field(default="", max_length=1000)


class UserReportSchema(BaseModel):
    user_id: str
    job_id: str
    reason: ReportReasonType
    note: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def serialize_evidence(evidence_dict: Dict[str, Any]) -> Dict[str, Any]:
    item = dict(evidence_dict)
    if isinstance(item.get("checked_at"), datetime):
        item["checked_at"] = item["checked_at"].isoformat()
    return item


def serialize_entity(entity_dict: Dict[str, Any]) -> Dict[str, Any]:
    if not entity_dict:
        return {"status": "needs_verification", "evidence": [], "missing": [], "warnings": []}
    res = dict(entity_dict)
    if "evidence" in res:
        res["evidence"] = [serialize_evidence(e) for e in res.get("evidence", [])]
    return res


def serialize_recruiter(recruiter_dict: Dict[str, Any]) -> Dict[str, Any]:
    if not recruiter_dict:
        return {
            "status": "needs_verification",
            "provided": False,
            "contact": {},
            "evidence": [],
            "missing": ["No recruiter information available"],
            "warnings": []
        }
    res = dict(recruiter_dict)
    if "evidence" in res:
        res["evidence"] = [serialize_evidence(e) for e in res.get("evidence", [])]
    return res


def serialize_verification(verif_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Serializes a MongoDB job_verification document into a clean API response."""
    if not verif_doc:
        return {}

    doc = dict(verif_doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))

    for date_key in ["checked_at", "next_check_after"]:
        val = doc.get(date_key)
        if isinstance(val, datetime):
            doc[date_key] = val.isoformat()

    doc["company"] = serialize_entity(doc.get("company", {}))
    doc["recruiter"] = serialize_recruiter(doc.get("recruiter", {}))
    doc["job"] = serialize_entity(doc.get("job", {}))

    # Serialize history items
    if "verification_history" in doc and isinstance(doc["verification_history"], list):
        clean_hist = []
        for h in doc["verification_history"]:
            item = dict(h)
            if isinstance(item.get("checked_at"), datetime):
                item["checked_at"] = item["checked_at"].isoformat()
            clean_hist.append(item)
        doc["verification_history"] = clean_hist

    return doc


def serialize_user_report(report_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Serializes a MongoDB user_reports document into clean API response."""
    if not report_doc:
        return {}
    doc = dict(report_doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    if isinstance(doc.get("created_at"), datetime):
        doc["created_at"] = doc["created_at"].isoformat()
    return doc
