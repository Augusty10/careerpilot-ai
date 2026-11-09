"""
Job-Specific Resume Customization Service for CareerPilot AI (Module 7).
Handles deterministic job requirement analysis, strict master profile fact whitelisting,
non-leaking skill gap isolation, AI-powered relevance synthesis, versioning,
diff computation, and draft approval lifecycle.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from bson import ObjectId

from backend.database import (
    get_resumes_collection,
    get_profiles_collection,
    get_jobs_collection,
    get_job_matches_collection,
    get_job_verifications_collection
)
from backend.services.skill_normalizer import normalize_skill
from backend.services.resume_validator import (
    extract_master_skills_set,
    validate_job_specific_customization
)
from backend.services.resume_export_service import export_resume_pdf_and_docx
from backend.services.ai_service import get_ai_service
from backend.models.resume import serialize_resume


def suggest_best_base_resume(user_id: str, job_doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates candidate's existing role-based resumes to recommend the best base resume
    for customizing against a specific job vacancy.
    """
    resumes_col = get_resumes_collection()
    role_resumes = list(resumes_col.find({
        "user_id": str(user_id),
        "kind": {"$ne": "job_specific"}
    }))

    if not role_resumes:
        return {
            "base_resume_id": None,
            "target_role": None,
            "reason": "No role-based resumes found. Generate a role resume first in Resume Hub."
        }

    job_title = job_doc.get("title", "").lower()
    job_skills = {normalize_skill(s) for s in job_doc.get("required_skills", []) if normalize_skill(s)}

    best_resume = None
    best_score = -1
    best_reason = ""

    for r in role_resumes:
        score = 0
        r_role = r.get("target_role", "").lower()
        if r_role in job_title or job_title in r_role:
            score += 10

        # Overlap with resume skills
        r_skills = set()
        for cat in r.get("content", {}).get("skills", []):
            for it in cat.get("items", []):
                norm = normalize_skill(it)
                if norm:
                    r_skills.add(norm)

        overlap = len(job_skills.intersection(r_skills))
        score += overlap * 2

        if score > best_score:
            best_score = score
            best_resume = r
            overlap_pct = int((overlap / len(job_skills) * 100)) if job_skills else 100
            best_reason = f"Shares {overlap_pct}% of required skills and aligns with target role '{r.get('target_role')}'."

    if not best_resume:
        best_resume = role_resumes[0]
        best_reason = f"Defaulting to latest role resume: {best_resume.get('target_role')}."

    return {
        "base_resume_id": str(best_resume["_id"]),
        "target_role": best_resume.get("target_role"),
        "version": best_resume.get("version", 1),
        "resume_name": best_resume.get("resume_name"),
        "reason": best_reason
    }


def _find_job_doc(jobs_col, job_id: str) -> Optional[Dict[str, Any]]:
    """Helper to locate a job doc by string job_id, ObjectId, or string _id."""
    job_doc = jobs_col.find_one({"job_id": str(job_id)})
    if not job_doc:
        try:
            job_doc = jobs_col.find_one({"_id": ObjectId(job_id)})
        except Exception:
            pass
    if not job_doc:
        try:
            job_doc = jobs_col.find_one({"_id": str(job_id)})
        except Exception:
            pass
    return job_doc


def analyze_job_and_profile(
    user_id: str,
    job_id: str,
    base_resume_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Performs comprehensive pre-generation gap analysis comparing the target job
    against the candidate's approved master career profile and chosen base resume.
    """
    profiles_col = get_profiles_collection()
    jobs_col = get_jobs_collection()
    resumes_col = get_resumes_collection()
    matches_col = get_job_matches_collection()
    verif_col = get_job_verifications_collection()

    # 1. Master Profile Check
    profile_doc = profiles_col.find_one({"user_id": str(user_id)})
    if not profile_doc or profile_doc.get("profile_status") != "approved":
        raise ValueError("An approved Master Career Profile is required. Please approve your profile in Profile Builder.")

    # 2. Job Check
    job_doc = _find_job_doc(jobs_col, job_id)
    if not job_doc:
        raise ValueError(f"Target job posting '{job_id}' not found.")

    # 3. Base Resume Check
    base_resume = None
    if base_resume_id:
        try:
            base_resume = resumes_col.find_one({
                "_id": ObjectId(base_resume_id),
                "user_id": str(user_id)
            })
        except Exception:
            pass
    if not base_resume:
        suggestion = suggest_best_base_resume(user_id, job_doc)
        if suggestion.get("base_resume_id"):
            base_resume = resumes_col.find_one({"_id": ObjectId(suggestion["base_resume_id"])})

    if not base_resume:
        raise ValueError("No role-based resume found. Please generate a role resume in Resume Hub before customizing.")

    # 4. Deterministic Skill Gap & Overlap Analysis
    master_skills_map = extract_master_skills_set(profile_doc)
    required_job_skills = job_doc.get("required_skills", [])

    matched_skills = []
    skill_gaps = []

    for raw_skill in required_job_skills:
        norm = normalize_skill(raw_skill)
        if norm and norm.lower() in master_skills_map:
            canonical = master_skills_map[norm.lower()]
            if canonical not in matched_skills:
                matched_skills.append(canonical)
        elif raw_skill.strip().lower() in master_skills_map:
            canonical = master_skills_map[raw_skill.strip().lower()]
            if canonical not in matched_skills:
                matched_skills.append(canonical)
        else:
            if raw_skill.strip() not in skill_gaps:
                skill_gaps.append(raw_skill.strip())

    # 5. Extract genuine technical keywords from job description
    desc_text = job_doc.get("description", "").lower()
    genuine_keywords = list(matched_skills)
    for kw, canon in master_skills_map.items():
        if len(kw) > 2 and kw in desc_text and canon not in genuine_keywords:
            genuine_keywords.append(canon)

    # 6. Prioritize Projects by Overlap
    master_projects = profile_doc.get("projects", [])
    prioritized_projects = []
    matched_set = {m.lower() for m in matched_skills}

    for idx, p in enumerate(master_projects):
        p_tech = [t for t in p.get("tech_stack", []) if isinstance(t, str)]
        p_tech_lower = {t.lower() for t in p_tech}
        overlap = list(matched_set.intersection(p_tech_lower))
        score = len(overlap)
        p_desc = p.get("description", "").lower()
        for kw in matched_set:
            if kw in p_desc:
                score += 1

        reason = f"Matches {len(overlap)} required technologies ({', '.join(overlap)})" if overlap else "Complementary software engineering project"
        prioritized_projects.append({
            "source_index": idx,
            "title": p.get("title", f"Project {idx+1}"),
            "tech_stack": p_tech,
            "score": score,
            "reason": reason
        })

    prioritized_projects.sort(key=lambda x: x["score"], reverse=True)

    # 7. Module 5 Matching & Module 6 Verification Context
    match_doc = matches_col.find_one({"user_id": str(user_id), "job_id": str(job_id)})
    verif_doc = verif_col.find_one({"job_id": str(job_id)})

    warnings = []
    if match_doc and match_doc.get("category") == "not_eligible":
        warnings.append(
            f"Eligibility Alert: You appear not to meet all stated criteria ({match_doc.get('explanation', 'Not eligible')}). Customization is permitted, but please review."
        )

    if verif_doc and verif_doc.get("overall_status") == "suspicious":
        warnings.append(
            "Safety Alert: This job posting has suspicious indicators (e.g. fee demands). Exercise caution before sharing your resume."
        )

    if job_doc.get("is_sample"):
        warnings.append("Sample Listing Note: This is a demo vacancy. Resumes generated for it are for testing.")

    exp_text = job_doc.get("experience_text", "0-1 years")
    cand_exp = profile_doc.get("work_experience", [])
    cand_intern = profile_doc.get("internships", [])
    exp_status = "match" if (cand_exp or cand_intern or "fresher" in exp_text.lower() or "0" in exp_text) else "potential_gap"
    exp_note = f"Candidate background aligns with entry-level requirement: {exp_text}"

    return {
        "job_id": str(job_id),
        "job_snapshot": {
            "title": job_doc.get("title"),
            "company": job_doc.get("company"),
            "location": job_doc.get("location"),
            "work_mode": job_doc.get("work_mode"),
            "application_url": job_doc.get("application_url"),
            "is_sample": job_doc.get("is_sample", False)
        },
        "base_resume": {
            "id": str(base_resume["_id"]),
            "target_role": base_resume.get("target_role"),
            "resume_name": base_resume.get("resume_name"),
            "version": base_resume.get("version", 1),
            "template": base_resume.get("template", "modern")
        },
        "matched_skills": matched_skills,
        "skill_gaps": skill_gaps,
        "keywords_included": genuine_keywords[:10],
        "projects_prioritized": prioritized_projects,
        "experience_alignment": {
            "status": exp_status,
            "note": exp_note
        },
        "warnings": warnings
    }


def customize_resume(
    user_id: str,
    job_id: str,
    base_resume_id: Optional[str] = None,
    template: str = "modern",
    resume_name: Optional[str] = None
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Executes the complete job-specific resume customization pipeline:
    1. Runs pre-generation gap analysis.
    2. Invokes AI tailoring with strict anti-hallucination prompts.
    3. Enforces post-generation validator (blocking skill gaps & metric invention).
    4. Computes versioning per (user_id, job_id).
    5. Saves as DRAFT and exports ATS PDF/DOCX to private storage.
    """
    profiles_col = get_profiles_collection()
    resumes_col = get_resumes_collection()
    jobs_col = get_jobs_collection()

    profile_doc = profiles_col.find_one({"user_id": str(user_id)})
    if not profile_doc or profile_doc.get("profile_status") != "approved":
        raise ValueError("An approved Master Career Profile is required. Please approve your profile in Profile Builder.")

    job_doc = _find_job_doc(jobs_col, job_id)
    if not job_doc:
        raise ValueError(f"Job posting '{job_id}' not found.")

    # 1. Pre-generation analysis
    analysis = analyze_job_and_profile(user_id, job_id, base_resume_id)
    matched_skills = analysis["matched_skills"]
    skill_gaps = analysis["skill_gaps"]
    genuine_keywords = analysis["keywords_included"]
    base_info = analysis["base_resume"]

    # 2. Determine Next Version per (user_id, job_id)
    existing_versions = resumes_col.find({
        "user_id": str(user_id),
        "job_id": str(job_id)
    }).sort("version", -1).limit(1)

    existing_ver_list = list(existing_versions)
    next_version = (existing_ver_list[0].get("version", 0) + 1) if existing_ver_list else 1

    # 3. AI Customization Step
    ai_service = get_ai_service()
    job_requirements = {
        "title": job_doc.get("title"),
        "company": job_doc.get("company"),
        "required_skills": matched_skills,
        "experience_text": job_doc.get("experience_text", "Entry Level"),
        "description": job_doc.get("description", "")
    }

    try:
        ai_res = ai_service.customize_resume_content(
            master_profile_facts=profile_doc,
            job_requirements=job_requirements,
            matched_keywords=genuine_keywords
        )
        custom_content = ai_res.get("content", {})
        changes_summary = ai_res.get("changes_summary", [])
    except Exception as e:
        # Fallback to mock deterministic generator
        from backend.services.ai_service import MockAIProvider
        ai_res = MockAIProvider().customize_resume_content(
            master_profile_facts=profile_doc,
            job_requirements=job_requirements,
            matched_keywords=genuine_keywords
        )
        custom_content = ai_res["content"]
        changes_summary = [
            {"section": "Notice", "change": "Deterministic reordering applied", "reason": "AI rewording unavailable"}
        ] + ai_res.get("changes_summary", [])

    # 4. Validate through extended validator (blocks skill gaps & metric invention)
    validated_content, validator_warnings = validate_job_specific_customization(
        resume_content=custom_content,
        master_profile=profile_doc,
        job_requirements=job_requirements,
        skill_gaps=skill_gaps
    )

    all_warnings = list(analysis["warnings"]) + validator_warnings

    # 5. Assemble Customization Metadata
    customization_meta = {
        "job_requirements": {
            "skills": job_doc.get("required_skills", []),
            "keywords": genuine_keywords[:8],
            "experience_text": job_doc.get("experience_text", ""),
            "education_text": job_doc.get("education_required", "")
        },
        "relevant_skills_highlighted": matched_skills,
        "projects_prioritized": [
            {"source_index": p["source_index"], "reason": p["reason"]}
            for p in analysis["projects_prioritized"]
        ],
        "keywords_included": genuine_keywords[:10],
        "skill_gaps": skill_gaps,
        "changes_summary": changes_summary,
        "experience_alignment": analysis["experience_alignment"],
        "generated_from_job_checked_at": job_doc.get("last_checked_at"),
        "generated_from_profile_updated_at": profile_doc.get("updated_at")
    }

    final_name = resume_name or f"{job_doc.get('company')} - {job_doc.get('title')} (v{next_version})"
    now = datetime.now(timezone.utc)

    resume_doc = {
        "user_id": str(user_id),
        "resume_name": final_name,
        "target_role": job_doc.get("title"),
        "version": next_version,
        "kind": "job_specific",
        "based_on_resume_id": str(base_info["id"]),
        "job_id": str(job_id),
        "job_snapshot": analysis["job_snapshot"],
        "content": validated_content,
        "template": template or base_info.get("template", "modern"),
        "customization": customization_meta,
        "approval_status": "draft",
        "approved_at": None,
        "created_at": now,
        "updated_at": now,
        "generated_from_profile_updated_at": profile_doc.get("updated_at")
    }

    # 6. Insert into MongoDB
    insert_res = resumes_col.insert_one(resume_doc)
    resume_id = str(insert_res.inserted_id)
    resume_doc["_id"] = insert_res.inserted_id

    # 7. Generate ATS PDF and DOCX files
    try:
        pdf_path, docx_path = export_resume_pdf_and_docx(
            user_id=str(user_id),
            resume_id=resume_id,
            content=validated_content,
            template=resume_doc["template"]
        )
        resumes_col.update_one(
            {"_id": insert_res.inserted_id},
            {"$set": {"pdf_path": pdf_path, "docx_path": docx_path}}
        )
    except Exception as exp_err:
        all_warnings.append(f"Export Notice: PDF/DOCX generation deferred ({exp_err}).")

    saved_doc = resumes_col.find_one({"_id": insert_res.inserted_id})
    serialized_resume = serialize_resume(saved_doc, master_profile_updated_at=profile_doc.get("updated_at"))
    diff_data = compute_resume_diff(base_info, saved_doc)

    return {
        "resume": serialized_resume,
        "diff": diff_data,
        "warnings": all_warnings
    }


def approve_customized_resume(user_id: str, resume_id: str) -> Dict[str, Any]:
    """
    Transitions a customized resume from 'draft' to 'approved' after candidate review.
    """
    resumes_col = get_resumes_collection()
    profiles_col = get_profiles_collection()

    try:
        r_oid = ObjectId(resume_id)
    except Exception:
        raise ValueError(f"Invalid resume ID: {resume_id}")

    resume_doc = resumes_col.find_one({"_id": r_oid, "user_id": str(user_id)})
    if not resume_doc:
        raise ValueError("Resume not found or access denied.")

    now = datetime.now(timezone.utc)
    resumes_col.update_one(
        {"_id": r_oid},
        {"$set": {
            "approval_status": "approved",
            "approved_at": now,
            "updated_at": now
        }}
    )

    profile_doc = profiles_col.find_one({"user_id": str(user_id)})
    updated = resumes_col.find_one({"_id": r_oid})
    return serialize_resume(updated, master_profile_updated_at=profile_doc.get("updated_at") if profile_doc else None)


def compute_resume_diff(
    base_resume: Dict[str, Any],
    customized_resume: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Computes a section-by-section diff between a base role resume and the customized resume.
    """
    base_content = base_resume.get("content", {})
    custom_content = customized_resume.get("content", {})

    # Summary diff
    summary_diff = {
        "base": base_content.get("summary", ""),
        "customized": custom_content.get("summary", ""),
        "changed": base_content.get("summary", "") != custom_content.get("summary", "")
    }

    # Skills diff
    base_skills = []
    for c in base_content.get("skills", []):
        base_skills.extend(c.get("items", []))

    custom_skills = []
    for c in custom_content.get("skills", []):
        custom_skills.extend(c.get("items", []))

    skills_diff = {
        "base_order": base_skills,
        "customized_order": custom_skills,
        "reordered": base_skills != custom_skills,
        "highlighted": customized_resume.get("customization", {}).get("relevant_skills_highlighted", [])
    }

    # Projects diff
    base_proj_titles = [p.get("title") for p in base_content.get("projects", [])]
    custom_proj_titles = [p.get("title") for p in custom_content.get("projects", [])]

    projects_diff = {
        "base_titles": base_proj_titles,
        "customized_titles": custom_proj_titles,
        "reordered": base_proj_titles != custom_proj_titles,
        "project_details": []
    }

    for idx, cp in enumerate(custom_content.get("projects", [])):
        src_idx = cp.get("source_index", idx)
        bp = base_content.get("projects", [])[src_idx] if src_idx < len(base_content.get("projects", [])) else {}
        projects_diff["project_details"].append({
            "title": cp.get("title"),
            "base_bullets": bp.get("description_bullets", []),
            "customized_bullets": cp.get("description_bullets", []),
            "bullets_changed": bp.get("description_bullets", []) != cp.get("description_bullets", [])
        })

    return {
        "summary": summary_diff,
        "skills": skills_diff,
        "projects": projects_diff,
        "changes_summary": customized_resume.get("customization", {}).get("changes_summary", []),
        "skill_gaps": customized_resume.get("customization", {}).get("skill_gaps", [])
    }


def list_job_resumes(user_id: str, job_id: str) -> List[Dict[str, Any]]:
    """Lists all job-specific resumes created by the candidate for a specific job."""
    resumes_col = get_resumes_collection()
    profiles_col = get_profiles_collection()

    profile_doc = profiles_col.find_one({"user_id": str(user_id)})
    p_time = profile_doc.get("updated_at") if profile_doc else None

    cursor = resumes_col.find({
        "user_id": str(user_id),
        "job_id": str(job_id),
        "kind": "job_specific"
    }).sort("version", -1)

    return [serialize_resume(doc, master_profile_updated_at=p_time) for doc in cursor]

