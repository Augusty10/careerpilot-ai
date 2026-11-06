import pytest
from datetime import datetime, timezone
from bson import ObjectId

from backend.services.skill_normalizer import normalize_skill, get_deterministic_related_skill
from backend.services.eligibility_rules import (
    check_education_qualification,
    check_graduation_year,
    check_experience_requirement,
    check_location_preference,
    evaluate_skills_and_coverage,
    determine_match_category
)
from backend.services.matching_service import compute_profile_version_hash, compute_match


def test_alias_normalization():
    """Verifies that common skill synonyms and aliases normalize to canonical keys."""
    assert normalize_skill("ReactJS") == "react"
    assert normalize_skill("React.js") == "react"
    assert normalize_skill("React") == "react"

    assert normalize_skill("Node") == "node.js"
    assert normalize_skill("Node.js") == "node.js"
    assert normalize_skill("NodeJS") == "node.js"

    assert normalize_skill("Postgres") == "postgresql"
    assert normalize_skill("PostgreSQL") == "postgresql"
    assert normalize_skill("MongoDB") == "mongodb"

    assert normalize_skill("Python3") == "python"
    assert normalize_skill("JS") == "javascript"
    assert normalize_skill("TailwindCSS") == "tailwind css"


def test_related_skills_partial_credit_mapping():
    """Verifies that recognized alternative frameworks are mapped as related technologies."""
    rel = get_deterministic_related_skill("django", "flask")
    assert rel is not None
    assert "alternative" in rel.lower() or "related" in rel.lower()

    # Testing symmetrical lookup
    rel_rev = get_deterministic_related_skill("flask", "django")
    assert rel_rev is not None

    rel_react_vue = get_deterministic_related_skill("react", "vue")
    assert rel_react_vue is not None


def test_education_parsing_and_unclear_handling():
    """Verifies parsing of standard degrees, 'Any graduate', and unparseable qualifications."""
    cand_btech = [{"degree": "B.Tech Computer Science", "institution": "IIT", "graduation_year": 2025}]

    # 1. Any graduate -> meets
    status, req, cand, hard_fail = check_education_qualification(cand_btech, "Any Graduate / Any Degree")
    assert status == "meets"
    assert not hard_fail

    # 2. Bachelor's degree -> meets
    status, req, cand, hard_fail = check_education_qualification(cand_btech, "Bachelor's degree in CS or equivalent")
    assert status == "meets"
    assert not hard_fail

    # 3. Master's degree required -> does_not_meet
    cand_diploma = [{"degree": "Diploma in IT", "institution": "Polytechnic", "graduation_year": 2023}]
    status, req, cand, hard_fail = check_education_qualification(cand_diploma, "Bachelor's degree required")
    assert status == "does_not_meet"
    assert hard_fail

    # 4. Unparseable education -> unclear (never not_eligible by guess)
    status, req, cand, hard_fail = check_education_qualification(cand_btech, "Specialized Guild Certification V3")
    assert status == "unclear"
    assert not hard_fail


def test_batch_year_matching_and_mismatch():
    """Verifies graduation batch matching and hard failure on mismatch."""
    cand_edu_2025 = [{"degree": "B.Tech", "institution": "XYZ", "graduation_year": 2025}]

    # Stated batch contains 2025 -> meets
    status, req, cand, hard_fail = check_graduation_year(
        cand_edu_2025,
        job_description="Hiring for 2024 / 2025 batch freshers. Great opportunity.",
        job_title="Software Engineer"
    )
    assert status == "meets"
    assert not hard_fail

    # Stated batch is 2022 / 2023 -> does_not_meet (hard failure)
    status, req, cand, hard_fail = check_graduation_year(
        cand_edu_2025,
        job_description="Only 2022 or 2023 passouts are eligible.",
        job_title="Associate"
    )
    assert status == "does_not_meet"
    assert hard_fail

    # No batch stated -> not_specified
    status, req, cand, hard_fail = check_graduation_year(
        cand_edu_2025,
        job_description="Looking for passionate developers with good problem solving skills.",
        job_title="Frontend Developer"
    )
    assert status == "not_specified"
    assert not hard_fail


def test_experience_rules_fresher_vs_senior():
    """Verifies fresher compatibility and hard failure when job requires 5+ years."""
    work_exp_empty = []
    internships = [{"company": "Tech Corp", "role": "Intern", "description": "Built APIs"}]

    # Fresher job (0-1 yrs) -> meets
    status, req, cand, hard_fail = check_experience_requirement(
        work_experience=work_exp_empty,
        internships=internships,
        job_min_years=0.0,
        job_max_years=1.0,
        job_fresher_status="fresher_friendly",
        job_experience_text="0-1 years"
    )
    assert status == "meets_stated_requirement"
    assert not hard_fail
    assert "Fresher" in cand

    # Senior job (5+ years) -> below_requirement and hard failure
    status, req, cand, hard_fail = check_experience_requirement(
        work_experience=work_exp_empty,
        internships=internships,
        job_min_years=5.0,
        job_max_years=8.0,
        job_fresher_status="experience_required",
        job_experience_text="5+ years"
    )
    assert status == "below_requirement"
    assert hard_fail


def test_location_mismatch_is_warning_not_hard_failure():
    """Verifies that location mismatch generates a warning without causing ineligibility."""
    cand_pref_locs = ["Bengaluru", "Remote"]

    # Remote job -> remote match
    status, req, cand, warning = check_location_preference(cand_pref_locs, "Bengaluru", "remote")
    assert status == "remote"
    assert warning is None

    # Matching city -> match
    status, req, cand, warning = check_location_preference(cand_pref_locs, "Bengaluru, Karnataka", "onsite")
    assert status == "match"
    assert warning is None

    # Mismatching city -> mismatch (warning only)
    status, req, cand, warning = check_location_preference(cand_pref_locs, "Hyderabad, Telangana", "onsite")
    assert status == "mismatch"
    assert warning is not None
    assert "Hyderabad" in warning


def test_deterministic_skill_matching_and_thresholds():
    """
    Candidate with Python, SQL, Flask, HTML vs Job requiring Python, SQL, Django.
    Python = match, SQL = match, Django = related (counts 0.5).
    Coverage = (2 + 0.5) / 3 = 83.3% -> strong_match (>= 75%).
    """
    candidate_skills = {"python", "sql", "flask", "html"}
    job_required = ["Python", "SQL", "Django"]

    matched, related, missing, coverage = evaluate_skills_and_coverage(
        candidate_skills=candidate_skills,
        job_required_skills=job_required
    )

    assert "Python" in matched
    assert "SQL" in matched
    assert len(related) == 1
    assert related[0]["job_skill"] == "Django"
    assert related[0]["candidate_skill"] == "flask"
    assert len(missing) == 0
    assert coverage == 83.3

    category = determine_match_category(
        hard_failures=[],
        skill_coverage=coverage,
        total_required_skills=3,
        strong_threshold=75,
        partial_threshold=40
    )
    assert category == "strong_match"


def test_job_with_no_skills_listed_limited_information():
    """Job with empty skills list assigns partial_match and labels limited information."""
    candidate_skills = {"python", "flask"}
    matched, related, missing, coverage = evaluate_skills_and_coverage(
        candidate_skills=candidate_skills,
        job_required_skills=[]
    )
    assert coverage is None

    category = determine_match_category(
        hard_failures=[],
        skill_coverage=coverage,
        total_required_skills=0
    )
    assert category == "partial_match"


def test_ai_cannot_upgrade_hard_failure():
    """A hard failure (e.g. 5 yrs experience required) must strictly output not_eligible regardless of skills."""
    category = determine_match_category(
        hard_failures=["Experience requirement not met: job requires 5+ years"],
        skill_coverage=100.0,
        total_required_skills=5
    )
    assert category == "not_eligible"


def test_end_to_end_match_lifecycle_and_staleness(app, client, clean_db):
    """
    End-to-end integration test:
    1. Register user and create approved profile.
    2. Seed a fresher job and a senior job.
    3. Compute match -> strong_match on fresher job, not_eligible on senior job.
    4. Verify no hiring probability text exists.
    5. Edit profile -> verify is_stale detection.
    6. Recompute -> verify is_stale clears.
    """
    # 1. Register & Login
    client.post("/api/auth/register", json={
        "name": "Dev Matcher",
        "email": "matcher@example.com",
        "password": "Password123"
    })
    login_resp = client.post("/api/auth/login", json={
        "email": "matcher@example.com",
        "password": "Password123"
    })
    token = login_resp.get_json()["token"]
    user_id = login_resp.get_json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Save and Approve Master Profile
    profile_data = {
        "personal": {
            "full_name": "Dev Matcher",
            "email": "matcher@example.com",
            "phone": "9876543210",
            "location": "Bengaluru, India"
        },
        "education": [{
            "degree": "B.Tech Computer Science",
            "institution": "National Institute",
            "graduation_year": 2025,
            "score_type": "cgpa",
            "score": 8.8
        }],
        "skills": {
            "languages": ["Python", "JavaScript", "SQL"],
            "frameworks": ["Flask", "React"],
            "databases": ["MongoDB"],
            "tools": ["Git"],
            "other": []
        },
        "projects": [{
            "title": "Backend API",
            "description": "Flask REST API with MongoDB",
            "tech_stack": ["Python", "Flask", "MongoDB"]
        }],
        "internships": [{
            "company": "Startup Hub",
            "role": "Backend Intern",
            "start_date": "2024-01",
            "end_date": "2024-06",
            "description": "Built endpoints"
        }],
        "certifications": [],
        "achievements": [],
        "work_experience": [],
        "preferred_roles": ["Python Developer", "Backend Developer"],
        "preferred_locations": ["Bengaluru", "Remote"]
    }
    client.put("/api/profile", json=profile_data, headers=headers)
    app_resp = client.post("/api/profile/approve", headers=headers)
    assert app_resp.status_code == 200

    # 3. Seed two jobs directly in MongoDB
    jobs_col = clean_db["jobs"]
    fresher_job_id = "test-job-fresher-001"
    senior_job_id = "test-job-senior-002"

    jobs_col.insert_one({
        "job_id": fresher_job_id,
        "title": "Junior Python Backend Developer",
        "normalized_title": "Junior Python Backend Developer",
        "company": "Acme Cloud",
        "location": "Bengaluru, India",
        "work_mode": "onsite",
        "job_type": "full_time",
        "experience_min_years": 0.0,
        "experience_max_years": 1.0,
        "fresher_status": "fresher_friendly",
        "education_required": "Bachelor's degree in CS or related field",
        "required_skills": ["Python", "Flask", "MongoDB", "Docker"],
        "description": "Hiring entry level Python developers. Freshers of 2024/2025 batch welcome.",
        "status": "active",
        "is_sample": True,
        "posted_at": datetime.now(timezone.utc).isoformat()
    })

    jobs_col.insert_one({
        "job_id": senior_job_id,
        "title": "Lead Software Architect",
        "normalized_title": "Lead Software Architect",
        "company": "Enterprise Corp",
        "location": "Hyderabad, India",
        "work_mode": "onsite",
        "job_type": "full_time",
        "experience_min_years": 6.0,
        "experience_max_years": 10.0,
        "fresher_status": "experience_required",
        "education_required": "Master's degree required",
        "required_skills": ["Python", "System Design", "Kubernetes", "AWS"],
        "description": "Requires at least 6+ years of full-time architecture experience.",
        "status": "active",
        "is_sample": True,
        "posted_at": datetime.now(timezone.utc).isoformat()
    })

    # 4. Compute Match on Fresher Job
    m1_resp = client.post(f"/api/matches/{fresher_job_id}", headers=headers)
    assert m1_resp.status_code == 200
    m1 = m1_resp.get_json()["match"]
    assert m1["category"] in ("strong_match", "partial_match")
    assert m1["skill_coverage"] == 75.0  # 3 of 4 skills: Python, Flask, MongoDB
    assert "Python" in m1["skills"]["matched"]
    assert "Docker" in m1["skills"]["missing"]
    assert m1["education"]["status"] == "meets"
    assert m1["experience"]["status"] == "meets_stated_requirement"
    assert len(m1["hard_failures"]) == 0

    # Verify no hiring probability text in explanation or disclaimer
    expl = m1["explanation"].lower()
    assert "probability" not in expl
    assert "chance of being hired" not in expl
    assert "prediction" not in expl
    assert "appears to meet" in expl or "strong" in expl

    # 5. Compute Match on Senior Job
    m2_resp = client.post(f"/api/matches/{senior_job_id}", headers=headers)
    assert m2_resp.status_code == 200
    m2 = m2_resp.get_json()["match"]
    assert m2["category"] == "not_eligible"
    assert len(m2["hard_failures"]) >= 1
    assert any("experience" in h.lower() for h in m2["hard_failures"])

    # 6. Staleness Check
    # Update candidate profile skills to add Docker
    profile_data["skills"]["tools"].append("Docker")
    client.put("/api/profile", json=profile_data, headers=headers)

    # Calling GET /api/matches/<job_id> should detect that profile changed
    stale_resp = client.get(f"/api/matches/{fresher_job_id}", headers=headers)
    assert stale_resp.status_code == 200
    stale_data = stale_resp.get_json()["match"]
    assert stale_data["is_stale"] is True

    # Re-approve profile and recompute match
    client.post("/api/profile/approve", headers=headers)
    recompute_resp = client.post(f"/api/matches/{fresher_job_id}", headers=headers)
    assert recompute_resp.status_code == 200
    refreshed = recompute_resp.get_json()["match"]
    assert refreshed["is_stale"] is False
    assert refreshed["skill_coverage"] == 100.0
    assert refreshed["category"] == "strong_match"

    # 7. Recommended Jobs Endpoint
    rec_resp = client.get("/api/jobs/recommended", headers=headers)
    assert rec_resp.status_code == 200
    rec_data = rec_resp.get_json()
    assert "jobs" in rec_data
    # Exclude not_eligible by default, so only the fresher job should be listed
    recommended_ids = [j["job"]["job_id"] for j in rec_data["jobs"]]
    assert fresher_job_id in recommended_ids
    assert senior_job_id not in recommended_ids


def test_batch_match_endpoint_and_limit(app, client, clean_db):
    """Verifies batch endpoint enforces 1-50 limit and tenant security."""
    client.post("/api/auth/register", json={
        "name": "Batch User",
        "email": "batch@example.com",
        "password": "Password123"
    })
    login_resp = client.post("/api/auth/login", json={
        "email": "batch@example.com",
        "password": "Password123"
    })
    token = login_resp.get_json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Batch with > 50 job IDs rejected
    oversized = [f"job-{i}" for i in range(51)]
    resp = client.post("/api/matches/batch", json={"job_ids": oversized}, headers=headers)
    assert resp.status_code == 400

    # Unauthenticated rejected
    resp_unauth = client.post("/api/matches/batch", json={"job_ids": ["job-1"]})
    assert resp_unauth.status_code == 401

    resp_unauth_get = client.get("/api/matches/job-1")
    assert resp_unauth_get.status_code == 401

    resp_unauth_rec = client.get("/api/jobs/recommended")
    assert resp_unauth_rec.status_code == 401


def test_tenant_isolation_job_matches(app, client, clean_db):
    """Verifies User B cannot access User A's computed matches."""
    # User A
    client.post("/api/auth/register", json={
        "name": "User Alpha", "email": "alpha@example.com", "password": "Password123"
    })
    log_a = client.post("/api/auth/login", json={"email": "alpha@example.com", "password": "Password123"})
    token_a = log_a.get_json()["token"]
    user_id_a = log_a.get_json()["user"]["id"]

    # User B
    client.post("/api/auth/register", json={
        "name": "User Beta", "email": "beta@example.com", "password": "Password123"
    })
    log_b = client.post("/api/auth/login", json={"email": "beta@example.com", "password": "Password123"})
    token_b = log_b.get_json()["token"]

    # Seed a match directly for User A
    matches_col = clean_db["job_matches"]
    matches_col.insert_one({
        "user_id": ObjectId(user_id_a),
        "job_id": "secret-job-123",
        "category": "strong_match",
        "skill_coverage": 90.0,
        "explanation": "Confidential match for Alpha only"
    })

    # User B listing matches should NOT see User A's match
    res_b = client.get("/api/matches", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    b_matches = res_b.get_json()["matches"]
    assert len(b_matches) == 0
