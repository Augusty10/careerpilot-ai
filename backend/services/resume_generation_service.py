"""
Resume Generation Service.
Orchestrates AI role-specific resume generation, truthfulness validation against
master profiles, version incrementing, MongoDB persistence, and ATS document export.
"""

import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from bson import ObjectId

from backend.database import get_profiles_collection, get_resumes_collection
from backend.services.ai_service import get_ai_service
from backend.services.resume_validator import validate_resume_against_master
from backend.services.resume_export_service import export_resume_pdf, export_resume_docx
from backend.models.resume import serialize_resume


DEFAULT_FRESHER_ROLES = [
    "Full Stack Developer",
    "Frontend Engineer",
    "Backend Developer",
    "Python Developer",
    "Data Analyst",
    "Software Engineer",
    "QA / Test Automation Engineer",
    "Cloud & DevOps Associate",
    "Cybersecurity Analyst",
    "Mobile App Developer"
]


def _get_private_resumes_dir(user_id: str) -> str:
    """Returns the absolute private storage directory for a user's resumes."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "private_storage", str(user_id), "resumes"))
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def _export_and_save_files(resume_doc: Dict[str, Any]) -> Tuple[str, str]:
    """Generates and writes both PDF and DOCX files for a resume document."""
    user_id = str(resume_doc["user_id"])
    resume_id = str(resume_doc["_id"])
    template = resume_doc.get("template", "modern")
    storage_dir = _get_private_resumes_dir(user_id)

    pdf_filename = f"{resume_id}_{template}.pdf"
    docx_filename = f"{resume_id}_{template}.docx"

    pdf_path = os.path.join(storage_dir, pdf_filename)
    docx_path = os.path.join(storage_dir, docx_filename)

    export_resume_pdf(resume_doc, pdf_path)
    export_resume_docx(resume_doc, docx_path)

    return pdf_path, docx_path


def generate_single_resume(
    user_id: str,
    target_role: str,
    template: str = "modern",
    resume_name: Optional[str] = None
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Generates a role-tailored resume from the candidate's approved master profile.
    Enforces truthfulness: master profile must be approved.
    Auto-increments version for (user_id, target_role).
    Exports PDF and DOCX files to private storage.
    """
    profiles_col = get_profiles_collection()
    resumes_col = get_resumes_collection()

    master_profile = profiles_col.find_one({"user_id": str(user_id)})
    if not master_profile:
        raise ValueError("Candidate profile not found. Please create and complete your master profile first.")

    if master_profile.get("profile_status") != "approved":
        raise ValueError("Master profile must be approved before generating role-specific resumes. Please review and approve your master profile.")

    # Determine version for this user and role
    existing_for_role = list(resumes_col.find({"user_id": str(user_id), "target_role": target_role}))
    max_version = max([r.get("version", 0) for r in existing_for_role], default=0)
    version = max_version + 1

    clean_name = (resume_name.strip() if resume_name and resume_name.strip() else f"{target_role} - v{version}")

    # Call AI service to tailor content to target role
    ai_service = get_ai_service()
    raw_content = ai_service.generate_role_tailored_resume(master_profile, target_role)

    # Strictly validate against master profile facts
    validated_content, warnings = validate_resume_against_master(raw_content, master_profile)

    now = datetime.now(timezone.utc)
    profile_updated_at = master_profile.get("updated_at")

    resume_doc = {
        "user_id": str(user_id),
        "resume_name": clean_name,
        "target_role": target_role,
        "version": version,
        "content": validated_content,
        "template": template if template in ["classic", "modern"] else "modern",
        "edited_by_user": False,
        "generated_from_profile_updated_at": profile_updated_at,
        "pdf_path": "",
        "docx_path": "",
        "created_at": now,
        "updated_at": now
    }

    insert_result = resumes_col.insert_one(resume_doc)
    resume_doc["_id"] = insert_result.inserted_id

    # Export PDF and DOCX
    try:
        pdf_path, docx_path = _export_and_save_files(resume_doc)
        resumes_col.update_one(
            {"_id": insert_result.inserted_id},
            {"$set": {"pdf_path": pdf_path, "docx_path": docx_path}}
        )
        resume_doc["pdf_path"] = pdf_path
        resume_doc["docx_path"] = docx_path
    except Exception as e:
        # File generation logging
        warnings.append(f"ATS export warning: {str(e)}")

    serialized = serialize_resume(resume_doc, master_profile.get("updated_at"))
    return serialized, warnings


def generate_multiple_resumes(
    user_id: str,
    target_roles: List[str],
    template: str = "modern"
) -> Tuple[List[Dict[str, Any]], Dict[str, List[str]]]:
    """
    Generates multiple resumes in batch (up to 5 roles).
    """
    if len(target_roles) > 5:
        raise ValueError("Maximum 5 resumes can be generated in a single batch.")

    results: List[Dict[str, Any]] = []
    all_warnings: Dict[str, List[str]] = {}

    for role in target_roles:
        res, warns = generate_single_resume(user_id, role, template=template)
        results.append(res)
        if warns:
            all_warnings[role] = warns

    return results, all_warnings


def update_resume(
    user_id: str,
    resume_id: str,
    update_data: Dict[str, Any]
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Updates an existing resume (edits summary, bullets, reorders skills, changes template).
    Enforces truthfulness against master profile. Re-exports PDF and DOCX.
    """
    resumes_col = get_resumes_collection()
    profiles_col = get_profiles_collection()

    resume = resumes_col.find_one({"_id": ObjectId(resume_id), "user_id": str(user_id)})
    if not resume:
        raise ValueError("Resume not found.")

    master_profile = profiles_col.find_one({"user_id": str(user_id)})
    if not master_profile:
        raise ValueError("Master profile not found.")

    warnings: List[str] = []
    set_fields: Dict[str, Any] = {
        "updated_at": datetime.now(timezone.utc),
        "edited_by_user": True
    }

    if "resume_name" in update_data and update_data["resume_name"]:
        set_fields["resume_name"] = str(update_data["resume_name"]).strip()

    if "template" in update_data and update_data["template"] in ["classic", "modern"]:
        set_fields["template"] = update_data["template"]

    if "content" in update_data and isinstance(update_data["content"], dict):
        validated_content, warns = validate_resume_against_master(update_data["content"], master_profile)
        warnings.extend(warns)
        set_fields["content"] = validated_content

    resumes_col.update_one({"_id": ObjectId(resume_id)}, {"$set": set_fields})
    updated_doc = resumes_col.find_one({"_id": ObjectId(resume_id)})

    # Re-export ATS documents
    try:
        pdf_path, docx_path = _export_and_save_files(updated_doc)
        resumes_col.update_one(
            {"_id": ObjectId(resume_id)},
            {"$set": {"pdf_path": pdf_path, "docx_path": docx_path}}
        )
        updated_doc["pdf_path"] = pdf_path
        updated_doc["docx_path"] = docx_path
    except Exception as e:
        warnings.append(f"ATS export warning: {str(e)}")

    serialized = serialize_resume(updated_doc, master_profile.get("updated_at"))
    return serialized, warnings


def duplicate_resume(user_id: str, resume_id: str) -> Dict[str, Any]:
    """
    Creates a new version from an existing resume.
    """
    resumes_col = get_resumes_collection()
    profiles_col = get_profiles_collection()

    orig = resumes_col.find_one({"_id": ObjectId(resume_id), "user_id": str(user_id)})
    if not orig:
        raise ValueError("Resume not found.")

    master_profile = profiles_col.find_one({"user_id": str(user_id)})
    target_role = orig.get("target_role", "Software Engineer")

    # Increment version
    existing_for_role = list(resumes_col.find({"user_id": str(user_id), "target_role": target_role}))
    max_version = max([r.get("version", 0) for r in existing_for_role], default=0)
    new_version = max_version + 1

    now = datetime.now(timezone.utc)
    new_doc = {
        "user_id": str(user_id),
        "resume_name": f"{orig.get('resume_name', target_role)} (v{new_version})",
        "target_role": target_role,
        "version": new_version,
        "content": orig.get("content", {}),
        "template": orig.get("template", "modern"),
        "edited_by_user": True,
        "generated_from_profile_updated_at": orig.get("generated_from_profile_updated_at"),
        "pdf_path": "",
        "docx_path": "",
        "created_at": now,
        "updated_at": now
    }

    insert_res = resumes_col.insert_one(new_doc)
    new_doc["_id"] = insert_res.inserted_id

    # Export PDF and DOCX
    pdf_path, docx_path = _export_and_save_files(new_doc)
    resumes_col.update_one(
        {"_id": insert_res.inserted_id},
        {"$set": {"pdf_path": pdf_path, "docx_path": docx_path}}
    )
    new_doc["pdf_path"] = pdf_path
    new_doc["docx_path"] = docx_path

    master_updated_at = master_profile.get("updated_at") if master_profile else None
    return serialize_resume(new_doc, master_updated_at)


def delete_resume(user_id: str, resume_id: str) -> bool:
    """
    Deletes a candidate resume document and removes its exported PDF/DOCX files.
    """
    resumes_col = get_resumes_collection()
    resume = resumes_col.find_one({"_id": ObjectId(resume_id), "user_id": str(user_id)})
    if not resume:
        return False

    # Remove files if present
    for path_key in ["pdf_path", "docx_path"]:
        file_path = resume.get(path_key)
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

    resumes_col.delete_one({"_id": ObjectId(resume_id)})
    return True


def get_resume_export_path(user_id: str, resume_id: str, format_type: str = "pdf") -> Tuple[str, str, str]:
    """
    Retrieves the local file path, mime type, and download filename for a resume.
    Re-generates the file on-the-fly if missing.
    Returns: (file_path, download_filename, mime_type)
    """
    resumes_col = get_resumes_collection()
    resume = resumes_col.find_one({"_id": ObjectId(resume_id), "user_id": str(user_id)})
    if not resume:
        raise ValueError("Resume not found.")

    target_role = resume.get("target_role", "Resume").replace(" ", "_")
    version = resume.get("version", 1)
    format_lower = format_type.lower()

    if format_lower == "pdf":
        file_path = resume.get("pdf_path")
        mime_type = "application/pdf"
        download_filename = f"{target_role}_Resume_v{version}.pdf"
        if not file_path or not os.path.exists(file_path):
            pdf_path, _ = _export_and_save_files(resume)
            resumes_col.update_one({"_id": resume["_id"]}, {"$set": {"pdf_path": pdf_path}})
            file_path = pdf_path
    elif format_lower == "docx":
        file_path = resume.get("docx_path")
        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        download_filename = f"{target_role}_Resume_v{version}.docx"
        if not file_path or not os.path.exists(file_path):
            _, docx_path = _export_and_save_files(resume)
            resumes_col.update_one({"_id": resume["_id"]}, {"$set": {"docx_path": docx_path}})
            file_path = docx_path
    else:
        raise ValueError("Unsupported format. Allowed: 'pdf', 'docx'.")

    return file_path, download_filename, mime_type

