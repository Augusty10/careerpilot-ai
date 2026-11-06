"""
Job Normalizer and Experience Parser.
Cleans raw job source dictionaries, extracts skills, normalizes titles,
parses experience ranges, classifies fresher friendliness, and prevents XSS.
"""

import re
import html
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone

from backend.models.job import JobSchema


# Curated canonical skill dictionary for fast, deterministic skill extraction
TECH_SKILLS_DICTIONARY = [
    # Languages
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "SQL", "HTML", "CSS", "Bash", "PHP", "Ruby",
    # Frameworks & Libraries
    "React", "Node.js", "Express", "Flask", "Django", "FastAPI", "Next.js", "Vue.js", "Angular", "Spring Boot",
    "Tailwind CSS", "Bootstrap", "jQuery", "Redux", "Pandas", "NumPy", "Scikit-Learn",
    # Databases & Storage
    "PostgreSQL", "MongoDB", "MySQL", "Redis", "SQLite", "Oracle", "Cassandra", "DynamoDB",
    # Tools & Platforms
    "Git", "GitHub", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Linux", "Postman", "Jira", "CI/CD",
    # QA & Testing
    "Selenium", "PyTest", "JUnit", "TestNG", "Manual Testing", "API Testing", "Automation Testing",
    # Cybersecurity & Networks
    "Wireshark", "Nmap", "SIEM", "Networking", "TCP/IP", "Vulnerability Assessment", "Network Security",
    # Analytics
    "Power BI", "Tableau", "Excel", "Data Analysis", "Data Cleaning", "REST APIs", "GraphQL"
]

SKILL_PATTERNS = {
    skill: re.compile(rf"(?<![\w\.\-])\b{re.escape(skill.lower())}\b(?![\w\.\-])", re.IGNORECASE)
    for skill in TECH_SKILLS_DICTIONARY
}


def sanitize_text(raw_text: str, max_length: int = 5000) -> str:
    """Strips HTML tags, unescapes entities, and clamps text length to prevent XSS and DB bloat."""
    if not raw_text or not isinstance(raw_text, str):
        return ""
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", raw_text)
    # Unescape HTML entities
    cleaned = html.unescape(cleaned)
    # Collapse multiple whitespaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:max_length]


def parse_experience(exp_text: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Parses experience text into numeric (min_years, max_years).
    Examples:
    - "0-1 years" -> (0.0, 1.0)
    - "Freshers" / "No experience" -> (0.0, 0.0)
    - "2+ yrs" -> (2.0, None)
    - "3-5 years" -> (3.0, 5.0)
    - "5 years" -> (5.0, 5.0)
    """
    if not exp_text or not isinstance(exp_text, str):
        return None, None

    text_lower = exp_text.lower().strip()

    # Immediate match for zero-experience indicators
    if any(k in text_lower for k in ["fresher", "no experience", "0 exp", "graduate trainee", "campus hire", "batch 2024", "batch 2025"]):
        if "0-1" in text_lower or "0 - 1" in text_lower:
            return 0.0, 1.0
        if "0-2" in text_lower or "0 - 2" in text_lower:
            return 0.0, 2.0
        return 0.0, 0.0

    # Range pattern: "0-1 years", "1 to 2 yrs", "3 - 5 Yrs"
    range_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)?", text_lower)
    if range_match:
        try:
            return float(range_match.group(1)), float(range_match.group(2))
        except ValueError:
            pass

    # Plus pattern: "2+ years", "3+ yrs", "5+ years"
    plus_match = re.search(r"(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?)?", text_lower)
    if plus_match:
        try:
            return float(plus_match.group(1)), None
        except ValueError:
            pass

    # Exact single number pattern: "5 years", "2 yrs experience"
    exact_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)", text_lower)
    if exact_match:
        try:
            val = float(exact_match.group(1))
            return val, val
        except ValueError:
            pass

    return None, None


def classify_fresher_status(
    title: str,
    experience_text: str,
    min_years: Optional[float],
    max_years: Optional[float],
    description: str = ""
) -> str:
    """
    Deterministically classifies job as:
    - 'fresher_friendly' (0 experience, trainee, freshers explicitly welcome)
    - 'entry_level' (0-2 years experience)
    - 'experience_required' (>2 years experience, senior, lead)
    - 'unclear' (ambiguous or unstated)
    """
    combined_header = f"{title} {experience_text}".lower()

    # Senior / Lead disqualifier
    if any(k in combined_header for k in ["senior", "lead", "principal", "architect", "manager", "staff engineer"]):
        return "experience_required"

    if min_years is not None:
        if min_years > 2.0:
            return "experience_required"
        if min_years <= 0.0 and (max_years is None or max_years <= 1.0):
            return "fresher_friendly"
        if min_years <= 1.0 and (max_years is None or max_years <= 2.0):
            return "entry_level"
        if min_years <= 2.0:
            return "entry_level"

    # Keyword inspection in header and description
    if any(k in combined_header for k in ["fresher", "intern", "graduate", "trainee", "campus", "entry level", "batch 2024", "batch 2025"]):
        return "fresher_friendly"

    if any(k in description.lower()[:300] for k in ["freshers welcome", "freshers can apply", "open for freshers", "no prior experience required"]):
        return "fresher_friendly"

    # Ambiguous/unstated experience
    return "unclear"


def extract_skills_from_text(text: str, existing_skills: Optional[List[str]] = None) -> List[str]:
    """Extracts recognizable technical skills using pre-compiled regex tokens."""
    found_skills = list(existing_skills or [])
    found_lower = {s.lower() for s in found_skills}

    for skill_name, pattern in SKILL_PATTERNS.items():
        if skill_name.lower() not in found_lower and pattern.search(text):
            found_skills.append(skill_name)
            found_lower.add(skill_name.lower())

    return found_skills


def normalize_title(raw_title: str) -> str:
    """Normalizes title for deduplication and indexing."""
    cleaned = re.sub(r"[^\w\s]", " ", raw_title.lower())
    cleaned = re.sub(r"\b(urgent|immediate|hiring|wanted|opening|full time|remote)\b", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_job_dict(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes a raw job dictionary into schema-valid attributes.
    Enforces URL validation, text sanitization, experience parsing, and fresher classification.
    """
    title = sanitize_text(raw.get("title", "Software Developer"), max_length=200)
    company = sanitize_text(raw.get("company", "Employer"), max_length=150)
    location = sanitize_text(raw.get("location", "Remote"), max_length=150)
    description = sanitize_text(raw.get("description", ""), max_length=5000)
    experience_text = sanitize_text(raw.get("experience_text", ""), max_length=200)
    education_required = sanitize_text(raw.get("education_required", ""), max_length=250)
    salary_text = sanitize_text(raw.get("salary_text", ""), max_length=150) if raw.get("salary_text") else None

    # Work mode normalization
    raw_work = str(raw.get("work_mode", "")).lower()
    if "remote" in raw_work or "remote" in location.lower():
        work_mode = "remote"
    elif "hybrid" in raw_work or "hybrid" in location.lower():
        work_mode = "hybrid"
    elif "onsite" in raw_work or "on-site" in raw_work or "office" in raw_work:
        work_mode = "onsite"
    else:
        work_mode = "unknown"

    # Job type normalization
    raw_type = str(raw.get("job_type", "")).lower()
    if "intern" in raw_type or "intern" in title.lower():
        job_type = "internship"
    elif "contract" in raw_type or "freelance" in raw_type:
        job_type = "contract"
    else:
        job_type = "full_time"

    # Experience parsing
    min_yrs, max_yrs = parse_experience(experience_text)
    if min_yrs is None and not experience_text:
        # Check description snippet for experience
        min_yrs, max_yrs = parse_experience(description[:300])

    # Fresher status
    fresher_status = classify_fresher_status(title, experience_text, min_yrs, max_yrs, description)

    # Skills extraction
    skills = extract_skills_from_text(
        text=f"{title} {description}",
        existing_skills=raw.get("required_skills", [])
    )

    # Application URL validation
    app_url = raw.get("application_url", "").strip()
    if not (app_url.startswith("http://") or app_url.startswith("https://")):
        app_url = f"https://example.com/job/{raw.get('job_id', 'unknown')}"

    now = datetime.now(timezone.utc)
    posted_at = raw.get("posted_at") or now
    deadline = raw.get("deadline")

    normalized = {
        "job_id": str(raw.get("job_id", "")),
        "title": title,
        "normalized_title": normalize_title(title),
        "company": company,
        "location": location,
        "work_mode": work_mode,
        "job_type": job_type,
        "experience_text": experience_text,
        "experience_min_years": min_yrs,
        "experience_max_years": max_yrs,
        "fresher_status": fresher_status,
        "education_required": education_required,
        "required_skills": skills[:25],
        "description": description,
        "salary_text": salary_text,
        "application_url": app_url,
        "source": str(raw.get("source", "unknown")),
        "is_sample": bool(raw.get("is_sample", False)),
        "posted_at": posted_at,
        "deadline": deadline,
        "status": str(raw.get("status", "active")),
        "first_seen_at": raw.get("first_seen_at", now),
        "last_checked_at": raw.get("last_checked_at", now),
        "duplicate_group_id": raw.get("duplicate_group_id")
    }

    # Validate through Pydantic
    validated = JobSchema(**normalized)
    return validated.model_dump()

