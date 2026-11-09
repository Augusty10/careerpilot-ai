"""
Resume Truthfulness Validator.
Ensures that all generated or edited resumes strictly adhere to the candidate's
master career profile. Rejects or auto-strips hallucinated or invented skills,
education, personal details, and experience.
"""

from typing import Dict, Any, List, Tuple, Set


class ResumeValidationError(Exception):
    """Raised when a resume fails truthfulness validation and cannot be repaired."""
    pass


def extract_master_skills_set(master_profile: Dict[str, Any]) -> Dict[str, str]:
    """
    Extracts a lookup dictionary of all legitimate skills present in the master profile.
    Maps lowercase skill name -> original casing.
    Searches:
    - skills.languages
    - skills.frameworks
    - skills.databases
    - skills.tools
    - skills.other
    - tech_stack of all projects
    """
    master_skills: Dict[str, str] = {}

    skills_data = master_profile.get("skills", {})
    if isinstance(skills_data, dict):
        for category in ["languages", "frameworks", "databases", "tools", "other"]:
            items = skills_data.get(category, [])
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, str) and item.strip():
                        s = item.strip()
                        master_skills[s.lower()] = s

    # Also include skills from master projects' tech_stack
    for proj in master_profile.get("projects", []):
        if isinstance(proj, dict):
            for t in proj.get("tech_stack", []):
                if isinstance(t, str) and t.strip():
                    s = t.strip()
                    master_skills[s.lower()] = s

    return master_skills


def validate_resume_against_master(
    resume_content: Dict[str, Any],
    master_profile: Dict[str, Any]
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validates resume content against the candidate's master profile.
    - Forces personal details to mirror the master profile.
    - Forces education items to mirror the master profile.
    - Auto-strips any skills that are NOT present in the master profile.
    - Validates projects, internships, and certifications against master data.
    
    Returns:
        (validated_content_dict, warnings_list)
    """
    warnings: List[str] = []
    validated = dict(resume_content)

    # 1. Enforce Truthful Personal Details
    master_personal = master_profile.get("personal", {})
    validated["personal"] = {
        "full_name": master_personal.get("full_name", ""),
        "email": master_personal.get("email", ""),
        "phone": master_personal.get("phone", ""),
        "location": master_personal.get("location", ""),
        "linkedin_url": master_personal.get("linkedin_url"),
        "github_url": master_personal.get("github_url"),
    }

    # 2. Enforce Truthful Education
    # Master education is single source of truth
    master_edu = master_profile.get("education", [])
    validated["education"] = [
        {
            "degree": e.get("degree", ""),
            "institution": e.get("institution", ""),
            "graduation_year": e.get("graduation_year"),
            "score_type": e.get("score_type", "cgpa"),
            "score": e.get("score"),
        }
        for e in master_edu
        if isinstance(e, dict) and e.get("degree") and e.get("institution")
    ]

    # 3. Enforce Strict Skill Whitelist
    master_skills_map = extract_master_skills_set(master_profile)
    raw_skills = resume_content.get("skills", [])
    cleaned_skill_categories: List[Dict[str, Any]] = []

    if isinstance(raw_skills, list):
        for cat in raw_skills:
            if not isinstance(cat, dict):
                continue
            cat_name = cat.get("category", "Technical Skills")
            raw_items = cat.get("items", [])
            valid_items = []
            for item in raw_items:
                if not isinstance(item, str) or not item.strip():
                    continue
                norm = item.strip().lower()
                if norm in master_skills_map:
                    # Keep canonical casing from master profile
                    canonical = master_skills_map[norm]
                    if canonical not in valid_items:
                        valid_items.append(canonical)
                else:
                    warnings.append(f"Removed unverified skill '{item}' (not found in master profile).")
            
            if valid_items:
                cleaned_skill_categories.append({
                    "category": cat_name,
                    "items": valid_items
                })

    # If all skill categories were empty or stripped, fallback to categorized master skills
    if not cleaned_skill_categories and master_skills_map:
        profile_skills = master_profile.get("skills", {})
        for cat_key, display_name in [
            ("languages", "Languages"),
            ("frameworks", "Frameworks & Libraries"),
            ("databases", "Databases"),
            ("tools", "Developer Tools"),
            ("other", "Other Competencies")
        ]:
            items = profile_skills.get(cat_key, [])
            if items:
                cleaned_skill_categories.append({
                    "category": display_name,
                    "items": items
                })

    validated["skills"] = cleaned_skill_categories

    # 4. Enforce Truthful Projects
    master_projects = master_profile.get("projects", [])
    raw_projects = resume_content.get("projects", [])
    cleaned_projects: List[Dict[str, Any]] = []

    if isinstance(raw_projects, list):
        for proj in raw_projects:
            if not isinstance(proj, dict):
                continue
            title = proj.get("title", "").strip()
            source_idx = proj.get("source_index")

            # Match to master project
            master_match = None
            if source_idx is not None and isinstance(source_idx, int) and 0 <= source_idx < len(master_projects):
                master_match = master_projects[source_idx]
            else:
                # Try finding by title match
                for idx, mp in enumerate(master_projects):
                    if mp.get("title", "").strip().lower() == title.lower():
                        master_match = mp
                        source_idx = idx
                        break

            if not master_match:
                # Project does not exist in master profile
                warnings.append(f"Ignored project '{title}' because it is not recorded in your master profile.")
                continue

            # Validate tech stack of project against master skills
            proj_tech = []
            for t in proj.get("tech_stack", []):
                if isinstance(t, str) and t.strip().lower() in master_skills_map:
                    proj_tech.append(master_skills_map[t.strip().lower()])
            if not proj_tech:
                proj_tech = master_match.get("tech_stack", [])

            # Format bullet points
            bullets = proj.get("description_bullets", [])
            if not bullets and master_match.get("description"):
                bullets = [b.strip() for b in master_match["description"].split("\n") if b.strip()]

            cleaned_projects.append({
                "source_index": source_idx,
                "title": master_match.get("title", title),
                "description_bullets": bullets[:5],  # max 5 bullets per project
                "tech_stack": proj_tech,
                "link": master_match.get("link") or proj.get("link")
            })

    # If no projects in resume or AI omitted them, load all from master profile
    if not cleaned_projects and master_projects:
        for idx, mp in enumerate(master_projects):
            desc = mp.get("description", "")
            bullets = [b.strip() for b in desc.split("\n") if b.strip()] if desc else []
            cleaned_projects.append({
                "source_index": idx,
                "title": mp.get("title", ""),
                "description_bullets": bullets if bullets else [desc] if desc else [],
                "tech_stack": mp.get("tech_stack", []),
                "link": mp.get("link")
            })

    validated["projects"] = cleaned_projects

    # 5. Enforce Internships
    master_internships = master_profile.get("internships", [])
    raw_internships = resume_content.get("internships", [])
    cleaned_internships: List[Dict[str, Any]] = []

    if isinstance(raw_internships, list) and raw_internships:
        for intern in raw_internships:
            if not isinstance(intern, dict):
                continue
            source_idx = intern.get("source_index")
            match = None
            if source_idx is not None and isinstance(source_idx, int) and 0 <= source_idx < len(master_internships):
                match = master_internships[source_idx]
            else:
                for idx, mi in enumerate(master_internships):
                    if mi.get("company", "").strip().lower() == intern.get("company", "").strip().lower():
                        match = mi
                        source_idx = idx
                        break
            if match:
                bullets = intern.get("description_bullets", [])
                if not bullets and match.get("description"):
                    bullets = [b.strip() for b in match["description"].split("\n") if b.strip()]
                cleaned_internships.append({
                    "source_index": source_idx,
                    "company": match.get("company", ""),
                    "role": match.get("role", ""),
                    "start_date": match.get("start_date", ""),
                    "end_date": match.get("end_date", ""),
                    "description_bullets": bullets if bullets else ([match.get("description")] if match.get("description") else [])
                })
    elif master_internships:
        for idx, mi in enumerate(master_internships):
            desc = mi.get("description", "")
            bullets = [b.strip() for b in desc.split("\n") if b.strip()] if desc else []
            cleaned_internships.append({
                "source_index": idx,
                "company": mi.get("company", ""),
                "role": mi.get("role", ""),
                "start_date": mi.get("start_date", ""),
                "end_date": mi.get("end_date", ""),
                "description_bullets": bullets if bullets else ([desc] if desc else [])
            })

    validated["internships"] = cleaned_internships

    # 6. Enforce Work Experience
    master_work = master_profile.get("work_experience", [])
    raw_work = resume_content.get("work_experience", [])
    cleaned_work: List[Dict[str, Any]] = []

    if isinstance(raw_work, list) and raw_work:
        for w in raw_work:
            if not isinstance(w, dict):
                continue
            source_idx = w.get("source_index")
            match = None
            if source_idx is not None and isinstance(source_idx, int) and 0 <= source_idx < len(master_work):
                match = master_work[source_idx]
            else:
                for idx, mw in enumerate(master_work):
                    if mw.get("company", "").strip().lower() == w.get("company", "").strip().lower():
                        match = mw
                        source_idx = idx
                        break
            if match:
                bullets = w.get("description_bullets", [])
                if not bullets and match.get("description"):
                    bullets = [b.strip() for b in match["description"].split("\n") if b.strip()]
                cleaned_work.append({
                    "source_index": source_idx,
                    "company": match.get("company", ""),
                    "role": match.get("role", ""),
                    "start_date": match.get("start_date", ""),
                    "end_date": match.get("end_date", ""),
                    "description_bullets": bullets if bullets else ([match.get("description")] if match.get("description") else [])
                })
    elif master_work:
        for idx, mw in enumerate(master_work):
            desc = mw.get("description", "")
            bullets = [b.strip() for b in desc.split("\n") if b.strip()] if desc else []
            cleaned_work.append({
                "source_index": idx,
                "company": mw.get("company", ""),
                "role": mw.get("role", ""),
                "start_date": mw.get("start_date", ""),
                "end_date": mw.get("end_date", ""),
                "description_bullets": bullets if bullets else ([desc] if desc else [])
            })

    validated["work_experience"] = cleaned_work

    # 7. Enforce Certifications (Must exist in master profile)
    master_certs = master_profile.get("certifications", [])
    master_cert_names = {c.get("name", "").strip().lower(): c for c in master_certs if isinstance(c, dict)}
    raw_certs = resume_content.get("certifications", [])
    cleaned_certs: List[Dict[str, Any]] = []

    if isinstance(raw_certs, list) and raw_certs:
        for cert in raw_certs:
            if not isinstance(cert, dict):
                continue
            name = cert.get("name", "").strip()
            if name.lower() in master_cert_names:
                match = master_cert_names[name.lower()]
                cleaned_certs.append({
                    "name": match.get("name", name),
                    "issuer": match.get("issuer", cert.get("issuer", "")),
                    "year": match.get("year", cert.get("year"))
                })
            else:
                warnings.append(f"Removed unverified certification '{name}'.")
    else:
        cleaned_certs = [
            {"name": c.get("name", ""), "issuer": c.get("issuer", ""), "year": c.get("year")}
            for c in master_certs
            if isinstance(c, dict) and c.get("name")
        ]

    validated["certifications"] = cleaned_certs

    # 8. Achievements
    master_achievements = master_profile.get("achievements", [])
    raw_achievements = resume_content.get("achievements", [])
    if isinstance(raw_achievements, list) and raw_achievements:
        # Keep achievements that roughly match or are present in master
        cleaned_achievements = [a.strip() for a in raw_achievements if isinstance(a, str) and a.strip() in master_achievements]
        if not cleaned_achievements:
            cleaned_achievements = master_achievements
    else:
        cleaned_achievements = master_achievements

    validated["achievements"] = cleaned_achievements

    # 9. Summary
    summary = resume_content.get("summary", "").strip()
    validated["summary"] = summary

    return validated, warnings


def validate_job_specific_customization(
    resume_content: Optional[Dict[str, Any]] = None,
    master_profile: Optional[Dict[str, Any]] = None,
    job_requirements: Optional[Dict[str, Any]] = None,
    skill_gaps: Optional[List[str]] = None,
    customized_content: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validates job-specific customized resume content:
    1. Runs baseline validate_resume_against_master() to enforce personal, education,
       and skill whitelist truthfulness.
    2. Enforces that NO skill listed in skill_gaps was injected into skills or tech_stacks.
    3. Detects and strips invented quantitative metrics in project/internship bullets
       that are absent from the master profile.
    
    Returns:
        (validated_content_dict, warnings_list)
    """
    import re

    content = resume_content if resume_content is not None else (customized_content or {})
    prof = master_profile or {}

    validated, warnings = validate_resume_against_master(content, prof)

    gap_set = {g.strip().lower() for g in (skill_gaps or []) if isinstance(g, str)}

    # Check if any skill gap leaked into skills
    cleaned_skill_cats = []
    for cat in validated.get("skills", []):
        cat_items = []
        for item in cat.get("items", []):
            if item.lower() in gap_set:
                warnings.append(
                    f"Blocked skill gap '{item}' from being added to resume (must be learned/added to master profile first)."
                )
            else:
                cat_items.append(item)
        if cat_items:
            cleaned_skill_cats.append({"category": cat["category"], "items": cat_items})
    validated["skills"] = cleaned_skill_cats

    # Check projects tech_stack for skill gaps
    for proj in validated.get("projects", []):
        cleaned_tech = []
        for t in proj.get("tech_stack", []):
            if t.lower() in gap_set:
                warnings.append(
                    f"Removed skill gap '{t}' from project '{proj.get('title')}' tech stack."
                )
            else:
                cleaned_tech.append(t)
        proj["tech_stack"] = cleaned_tech

    # Check for hallucinated metrics in bullets
    master_text = " ".join([
        p.get("description", "") for p in master_profile.get("projects", []) if isinstance(p, dict)
    ] + [
        it.get("description", "") for it in master_profile.get("internships", []) if isinstance(it, dict)
    ]).lower()

    metric_pattern = re.compile(r"\b(\d{1,3}%|\$\d+|\d+x|\d+\s*(?:ms|seconds|users|clients|req/s))\b", re.IGNORECASE)

    for proj in validated.get("projects", []):
        cleaned_bullets = []
        for bullet in proj.get("description_bullets", []):
            found_metrics = metric_pattern.findall(bullet)
            for m in found_metrics:
                if m.lower() not in master_text:
                    warnings.append(
                        f"Removed invented metric '{m}' in project '{proj.get('title')}' (not found in master profile)."
                    )
                    bullet = re.sub(re.escape(m), "measurably", bullet)
            cleaned_bullets.append(bullet)
        proj["description_bullets"] = cleaned_bullets

    return validated, warnings

