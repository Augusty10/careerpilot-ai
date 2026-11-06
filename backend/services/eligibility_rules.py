import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set
from backend.services.skill_normalizer import normalize_skill, get_deterministic_related_skill


# Degree level weights
DEGREE_LEVELS = {
    "doctorate": 4,
    "master": 3,
    "bachelor": 2,
    "diploma": 1,
    "high_school": 0
}

DEGREE_SYNONYMS = {
    # Doctorate
    "phd": "doctorate",
    "ph.d": "doctorate",
    "doctorate": "doctorate",

    # Master
    "m.tech": "master",
    "mtech": "master",
    "m.e.": "master",
    "me": "master",
    "mca": "master",
    "ms": "master",
    "m.s.": "master",
    "m.sc": "master",
    "msc": "master",
    "mba": "master",
    "master": "master",
    "post graduate": "master",
    "postgraduate": "master",

    # Bachelor
    "b.tech": "bachelor",
    "btech": "bachelor",
    "b.e.": "bachelor",
    "be": "bachelor",
    "bca": "bachelor",
    "b.sc": "bachelor",
    "bsc": "bachelor",
    "b.com": "bachelor",
    "bcom": "bachelor",
    "bba": "bachelor",
    "bachelor": "bachelor",
    "graduate": "bachelor",
    "degree": "bachelor",
    "undergraduate": "bachelor",

    # Diploma
    "diploma": "diploma",
    "polytechnic": "diploma",

    # High School
    "12th": "high_school",
    "hsc": "high_school",
    "intermediate": "high_school",
    "10th": "high_school",
    "ssc": "high_school"
}


def parse_degree_level(degree_text: str) -> Optional[str]:
    """Extracts degree level category (doctorate, master, bachelor, diploma, high_school) from text."""
    if not degree_text:
        return None

    clean = degree_text.strip().lower()

    # Direct keyword matches
    for keyword, level in DEGREE_SYNONYMS.items():
        if re.search(r"\b" + re.escape(keyword) + r"\b", clean):
            return level

    return None


def get_highest_candidate_education(education_list: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Finds highest degree level and corresponding education record from candidate profile."""
    if not education_list:
        return None, None

    highest_level = None
    highest_rank = -1
    highest_record = None

    for edu in education_list:
        degree_str = edu.get("degree", "")
        level = parse_degree_level(degree_str)
        rank = DEGREE_LEVELS.get(level, -1) if level else -1
        if rank > highest_rank:
            highest_rank = rank
            highest_level = level
            highest_record = edu

    return highest_level, highest_record


def check_education_qualification(
    candidate_education: List[Dict[str, Any]],
    job_education_text: Optional[str]
) -> Tuple[str, str, str, bool]:
    """
    Compares candidate education against job requirements.
    Returns: (status, job_requirement, candidate_value, is_hard_failure)
    Status: "meets" | "does_not_meet" | "unclear" | "not_specified"
    """
    highest_level, highest_record = get_highest_candidate_education(candidate_education)
    candidate_val = (
        f"{highest_record.get('degree', 'Unknown')} from {highest_record.get('institution', 'Unknown')}"
        if highest_record else "No education listed"
    )

    if not job_education_text or not job_education_text.strip():
        return "not_specified", "Not specified in job listing", candidate_val, False

    job_text_clean = job_education_text.strip().lower()
    job_req = job_education_text.strip()

    # "Any graduate" or "Any degree" pattern
    if re.search(r"\bany\s+(graduate|degree|discipline|branch|stream)\b", job_text_clean):
        if highest_level in ("bachelor", "master", "doctorate"):
            return "meets", job_req, candidate_val, False
        elif highest_level in ("diploma", "high_school"):
            return "does_not_meet", job_req, candidate_val, True
        else:
            return "unclear", job_req, candidate_val, False

    # Extract required level
    job_req_level = parse_degree_level(job_text_clean)

    if not job_req_level:
        # Unparseable education requirement -> return unclear, NEVER guess does_not_meet!
        return "unclear", job_req, candidate_val, False

    if not highest_level:
        return "unclear", job_req, candidate_val, False

    cand_rank = DEGREE_LEVELS.get(highest_level, 0)
    job_rank = DEGREE_LEVELS.get(job_req_level, 0)

    if cand_rank >= job_rank:
        return "meets", job_req, candidate_val, False
    else:
        # Clearly below required educational rank (e.g. Diploma when Bachelor is required)
        is_hard_fail = (job_rank - cand_rank >= 1)
        return "does_not_meet", job_req, candidate_val, is_hard_fail


def check_graduation_year(
    candidate_education: List[Dict[str, Any]],
    job_description: Optional[str],
    job_title: Optional[str] = None
) -> Tuple[str, str, Optional[int], bool]:
    """
    Detects batch/graduation year eligibility from job details.
    Returns: (status, job_requirement, candidate_value, is_hard_failure)
    Status: "meets" | "does_not_meet" | "not_specified" | "unclear"
    """
    highest_level, highest_record = get_highest_candidate_education(candidate_education)
    cand_year = highest_record.get("graduation_year") if highest_record else None

    combined_text = f"{job_title or ''} {job_description or ''}"

    # Match patterns like: "2024 / 2025 batch", "2024 or 2025 passouts", "Batch of 2024", "2023/2024/2025 graduates"
    batch_pattern = re.compile(
        r"\b(?:batch\s*(?:of)?\s*)?(202[0-9])(?:\s*(?:/|-|,|or|&)\s*(202[0-9]))?(?:\s*(?:/|-|,|or|&)\s*(202[0-9]))?\s*(?:batch|passout|passouts|graduates|graduating|pass out)?\b",
        re.IGNORECASE
    )

    eligible_years: Set[int] = set()

    for match in batch_pattern.finditer(combined_text):
        snippet = combined_text[max(0, match.start() - 15):min(len(combined_text), match.end() + 15)].lower()
        # Ensure context indicates batch/graduation
        if any(term in snippet for term in ("batch", "passout", "graduat", "eligible", "eligibility", "fresh")):
            for g in match.groups():
                if g:
                    eligible_years.add(int(g))

    if not eligible_years:
        return "not_specified", "Not specified in job listing", cand_year, False

    job_req = f"Batch: {', '.join(map(str, sorted(eligible_years)))}"

    if cand_year is None:
        return "unclear", job_req, cand_year, False

    if cand_year in eligible_years:
        return "meets", job_req, cand_year, False
    else:
        # Explicit batch requirement not met -> hard failure
        return "does_not_meet", job_req, cand_year, True


def calculate_candidate_fulltime_experience_years(work_experience: List[Dict[str, Any]]) -> float:
    """
    Calculates total years of full-time work experience from dates.
    Internships are NOT counted as full-time years.
    """
    if not work_experience:
        return 0.0

    total_months = 0
    now = datetime.now()

    for item in work_experience:
        start_str = item.get("start_date", "")
        end_str = item.get("end_date", "")

        # Try parsing YYYY-MM or YYYY
        start_dt = None
        for fmt in ("%Y-%m", "%Y/%m", "%m/%Y", "%Y"):
            try:
                start_dt = datetime.strptime(start_str.strip(), fmt)
                break
            except Exception:
                pass

        if not start_dt:
            continue

        end_dt = None
        if end_str and end_str.strip().lower() in ("present", "current", "till date"):
            end_dt = now
        elif end_str:
            for fmt in ("%Y-%m", "%Y/%m", "%m/%Y", "%Y"):
                try:
                    end_dt = datetime.strptime(end_str.strip(), fmt)
                    break
                except Exception:
                    pass

        if not end_dt:
            end_dt = now

        months = max(1, (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month))
        total_months += months

    return round(total_months / 12.0, 1)


def check_experience_requirement(
    work_experience: List[Dict[str, Any]],
    internships: List[Dict[str, Any]],
    job_min_years: Optional[float],
    job_max_years: Optional[float],
    job_fresher_status: Optional[str],
    job_experience_text: Optional[str]
) -> Tuple[str, str, str, bool]:
    """
    Compares candidate experience against job requirements.
    Returns: (status, job_requirement, candidate_value, is_hard_failure)
    Status: "meets_stated_requirement" | "below_requirement" | "not_specified"
    """
    cand_fulltime_years = calculate_candidate_fulltime_experience_years(work_experience)
    internship_count = len(internships) if internships else 0

    if cand_fulltime_years == 0.0:
        if internship_count > 0:
            cand_val = f"Fresher (0 years full-time, {internship_count} internship{'s' if internship_count > 1 else ''})"
        else:
            cand_val = "Fresher (0 years full-time)"
    else:
        cand_val = f"{cand_fulltime_years} year{'s' if cand_fulltime_years != 1 else ''} full-time"

    # Formulate job requirement description
    if job_min_years is not None and job_max_years is not None:
        job_req = f"{job_min_years}-{job_max_years} years"
    elif job_min_years is not None:
        job_req = f"{job_min_years}+ years"
    elif job_experience_text:
        job_req = job_experience_text.strip()
    else:
        job_req = "Not specified"

    # If job has no stated experience criteria
    if job_min_years is None and not job_experience_text:
        return "not_specified", job_req, cand_val, False

    # Fresher candidate evaluations
    if cand_fulltime_years == 0.0:
        # Jobs tagged as fresher_friendly, entry_level, or <= 1 year min experience
        if job_fresher_status in ("fresher_friendly", "entry_level") or (job_min_years is not None and job_min_years <= 1.0):
            return "meets_stated_requirement", job_req, cand_val, False
        elif job_min_years is not None and job_min_years > 1.0:
            # Hard requirement fails: candidate is a fresher but job requires 2+, 3+, 5+ years
            is_hard_fail = (job_min_years > cand_fulltime_years + 1.0)
            return "below_requirement", job_req, cand_val, is_hard_fail
        else:
            return "meets_stated_requirement", job_req, cand_val, False

    # Candidate with full-time experience
    effective_min = job_min_years if job_min_years is not None else 0.0
    if cand_fulltime_years >= effective_min:
        return "meets_stated_requirement", job_req, cand_val, False
    else:
        is_hard_fail = (effective_min > cand_fulltime_years + 1.0)
        return "below_requirement", job_req, cand_val, is_hard_fail


def check_location_preference(
    candidate_preferred_locations: List[str],
    job_location: Optional[str],
    job_work_mode: Optional[str]
) -> Tuple[str, str, Any, Optional[str]]:
    """
    Compares job location and work mode with candidate preferences.
    Returns: (status, job_requirement, candidate_value, warning_message)
    Status: "match" | "mismatch" | "remote" | "not_specified"
    """
    job_loc_str = job_location.strip() if job_location else "Unspecified"
    pref_locations = candidate_preferred_locations or []

    # Remote jobs match any candidate location
    if job_work_mode == "remote" or "remote" in job_loc_str.lower():
        return "remote", f"{job_loc_str} (Remote)", pref_locations, None

    if not pref_locations:
        return "not_specified", job_loc_str, "No preferred locations set", None

    # Normalization check
    norm_job_loc = re.sub(r"[,\-\.]", " ", job_loc_str.lower())
    matched = False
    for pref in pref_locations:
        norm_pref = pref.strip().lower()
        if norm_pref == "remote":
            continue
        if norm_pref in norm_job_loc:
            matched = True
            break
        # Common city aliases: Bangalore <-> Bengaluru, Bombay <-> Mumbai, etc.
        if norm_pref in ("bangalore", "bengaluru") and any(b in norm_job_loc for b in ("bangalore", "bengaluru")):
            matched = True
            break
        if norm_pref in ("mumbai", "bombay") and any(m in norm_job_loc for m in ("mumbai", "bombay")):
            matched = True
            break
        if norm_pref in ("delhi", "ncr", "gurgaon", "noida") and any(d in norm_job_loc for d in ("delhi", "ncr", "gurgaon", "noida")):
            matched = True
            break

    if matched:
        return "match", job_loc_str, pref_locations, None
    else:
        warning_msg = f"Location mismatch: Job is located in {job_loc_str}, while your preferred locations are {', '.join(pref_locations)}."
        return "mismatch", job_loc_str, pref_locations, warning_msg


def check_job_type_preference(
    candidate_preferred_roles: List[str],
    job_type: Optional[str]
) -> Tuple[str, str, Any, Optional[str]]:
    """
    Checks if job_type aligns with candidate preferences.
    Status: "match" | "mismatch" | "not_specified"
    """
    if not job_type or job_type == "unknown":
        return "not_specified", "Not specified", "Not specified", None

    clean_type = job_type.strip().lower()
    return "match", clean_type.replace("_", " ").title(), "Compatible", None


def check_certifications_requirement(
    candidate_certifications: List[Dict[str, Any]],
    job_description: Optional[str]
) -> Tuple[str, List[str], Optional[str], bool]:
    """
    Checks if job explicitly mandates certifications and whether candidate possesses them.
    Status: "meets" | "missing" | "not_specified"
    """
    if not job_description:
        return "not_specified", [], None, False

    desc_clean = job_description.lower()

    # Identify mandated certification phrases (e.g. "must have AWS Certified", "CCNA required")
    mandatory_keywords = [
        "aws certified", "ccna", "cissp", "pmp", "ceh", "certified kubernetes administrator",
        "cka", "azure certified", "gcp certified"
    ]

    required_certs = []
    for cert in mandatory_keywords:
        pattern = r"\b(mandatory|must have|required|prerequisite)\b.*?\b" + re.escape(cert) + r"\b"
        reverse_pattern = r"\b" + re.escape(cert) + r"\b.*?\b(mandatory|is required|required)\b"
        if re.search(pattern, desc_clean) or re.search(reverse_pattern, desc_clean):
            required_certs.append(cert.upper())

    if not required_certs:
        return "not_specified", [], None, False

    candidate_cert_names = [
        c.get("name", "").lower() for c in candidate_certifications or []
    ]

    missing = []
    for req in required_certs:
        if not any(req.lower() in cand_c for cand_c in candidate_cert_names):
            missing.append(req)

    if missing:
        return "missing", missing, ", ".join(required_certs), True
    else:
        return "meets", [], ", ".join(required_certs), False


def extract_candidate_skills_set(candidate_profile: Dict[str, Any]) -> Set[str]:
    """Extracts and normalizes all technical skills from candidate profile categories and project tech stacks."""
    skills_set: Set[str] = set()

    skills_dict = candidate_profile.get("skills", {})
    if isinstance(skills_dict, dict):
        for cat in ("languages", "frameworks", "databases", "tools", "other"):
            for item in skills_dict.get(cat, []):
                norm = normalize_skill(item)
                if norm:
                    skills_set.add(norm)

    # Also include project tech stacks
    for proj in candidate_profile.get("projects", []):
        for item in proj.get("tech_stack", []):
            norm = normalize_skill(item)
            if norm:
                skills_set.add(norm)

    return skills_set


def evaluate_skills_and_coverage(
    candidate_skills: Set[str],
    job_required_skills: List[str],
    semantic_related_dict: Optional[Dict[str, str]] = None
) -> Tuple[List[str], List[Dict[str, str]], List[str], Optional[float]]:
    """
    Evaluates required job skills against candidate skills:
    - Exact/Alias matches -> matched
    - Related skills (via semantic_related_dict or deterministic lookup) -> related
    - Unmatched -> missing
    Returns: (matched_skills, related_skills, missing_skills, skill_coverage_pct)
    """
    if not job_required_skills:
        return [], [], [], None

    matched: List[str] = []
    related: List[Dict[str, str]] = []
    missing: List[str] = []

    semantic_dict = semantic_related_dict or {}

    for raw_skill in job_required_skills:
        norm_skill = normalize_skill(raw_skill)
        if not norm_skill:
            continue

        if norm_skill in candidate_skills:
            matched.append(raw_skill)
        else:
            # Check semantic/deterministic related skills
            found_related = False

            # Check provided semantic dict first
            if norm_skill in semantic_dict:
                cand_related_skill = semantic_dict[norm_skill]
                related.append({
                    "job_skill": raw_skill,
                    "candidate_skill": cand_related_skill,
                    "relationship": f"Related skill to {raw_skill}"
                })
                found_related = True
            else:
                # Deterministic alias/family lookup
                for cand_skill in candidate_skills:
                    rel_desc = get_deterministic_related_skill(norm_skill, cand_skill)
                    if rel_desc:
                        related.append({
                            "job_skill": raw_skill,
                            "candidate_skill": cand_skill,
                            "relationship": rel_desc
                        })
                        found_related = True
                        break

            if not found_related:
                missing.append(raw_skill)

    total_req = len(matched) + len(related) + len(missing)
    if total_req == 0:
        coverage = None
    else:
        # Exact counts as 1.0, related counts as 0.5 (half credit, never full)
        raw_coverage = (len(matched) + 0.5 * len(related)) / float(total_req) * 100.0
        coverage = round(min(100.0, raw_coverage), 1)

    return matched, related, missing, coverage


def determine_match_category(
    hard_failures: List[str],
    skill_coverage: Optional[float],
    total_required_skills: int,
    strong_threshold: int = 75,
    partial_threshold: int = 40
) -> str:
    """
    Determines overall match category strictly rule-based:
    - "not_eligible": Any hard requirement fails.
    - "strong_match": No hard failures AND coverage >= strong_threshold.
    - "partial_match": No hard failures AND coverage between partial_threshold and strong_threshold.
    - "low_match": No hard failures AND coverage < partial_threshold.
    """
    if hard_failures:
        return "not_eligible"

    if total_required_skills == 0 or skill_coverage is None:
        # Limited information available
        return "partial_match"

    if skill_coverage >= strong_threshold:
        return "strong_match"
    elif skill_coverage >= partial_threshold:
        return "partial_match"
    else:
        return "low_match"
