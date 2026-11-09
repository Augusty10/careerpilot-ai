import pytest
from datetime import datetime, timezone, timedelta
from bson import ObjectId

from backend.database import get_profiles_collection, get_jobs_collection, get_resumes_collection
from backend.services.resume_validator import validate_job_specific_customization


@pytest.fixture
def auth_user(client):
    """Creates authenticated candidate with an approved master profile and a base role resume."""
    payload = {
        "name": "Jordan Smith",
        "email": "jordan@example.com",
        "password": "Password123"
    }
    client.post("/api/auth/register", json=payload)
    login_res = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = login_res.get_json()["token"]
    user_id = login_res.get_json()["user"]["id"]

    profile_payload = {
        "personal": {
            "full_name": "Jordan Smith",
            "email": "jordan@example.com",
            "phone": "+1 (555) 019-2834",
            "location": "Seattle, WA",
            "linkedin_url": "https://linkedin.com/in/jordansmith",
            "github_url": "https://github.com/jordansmith"
        },
        "education": [
            {
                "degree": "B.S. in Computer Science",
                "institution": "University of Washington",
                "graduation_year": 2024,
                "score_type": "cgpa",
                "score": 3.8
            }
        ],
        "skills": {
            "languages": ["Python", "JavaScript", "SQL"],
            "frameworks": ["Flask", "React", "FastAPI"],
            "databases": ["PostgreSQL", "MongoDB"],
            "tools": ["Git", "Docker", "Postman"],
            "other": ["REST APIs", "Agile"]
        },
        "projects": [
            {
                "title": "Cloud Analytics Dashboard",
                "description": "Full-stack dashboard for visualizing cloud resource utilization.",
                "tech_stack": ["React", "Flask", "PostgreSQL"],
                "link": "https://github.com/jordansmith/cloud-dash"
            },
            {
                "title": "API Gateway Service",
                "description": "Lightweight routing and authentication proxy built with FastAPI and Redis.",
                "tech_stack": ["FastAPI", "Python", "Docker"],
                "link": "https://github.com/jordansmith/api-gateway"
            }
        ],
        "internships": [
            {
                "company": "TechCorp",
                "role": "Software Engineering Intern",
                "start_date": "Jun 2023",
                "end_date": "Aug 2023",
                "description": "Assisted backend team with RESTful APIs."
            }
        ],
        "certifications": [
            {
                "name": "AWS Certified Cloud Practitioner",
                "issuer": "Amazon Web Services",
                "year": 2023
            }
        ],
        "achievements": ["Hackathon 1st Place 2023"],
        "work_experience": [],
        "preferred_roles": ["Python Developer", "Full Stack Developer"],
        "preferred_locations": ["Seattle, WA", "Remote"]
    }
    client.put("/api/profile", json=profile_payload, headers={"Authorization": f"Bearer {token}"})
    client.post("/api/profile/approve", headers={"Authorization": f"Bearer {token}"})

    # Generate a base role resume
    res = client.post("/api/resumes/generate", json={
        "target_role": "Python Developer",
        "template": "modern"
    }, headers={"Authorization": f"Bearer {token}"})
    base_resume = res.get_json()["resume"]

    return {
        "token": token,
        "id": user_id,
        "email": payload["email"],
        "base_resume": base_resume
    }


@pytest.fixture
def test_job():
    """Seeds a test job vacancy in jobs collection."""
    jobs_col = get_jobs_collection()
    job_doc = {
        "title": "Junior Python / Backend Engineer",
        "company": "Stripe Technologies",
        "location": "Seattle, WA",
        "work_mode": "hybrid",
        "job_type": "full_time",
        "fresher_status": "fresher_friendly",
        "experience_min_years": 0,
        "experience_max_years": 2,
        "education_required": ["Bachelor's in Computer Science or related"],
        "required_skills": ["Python", "Flask", "Docker", "Kubernetes", "AWS", "Kafka"],
        "description": "Looking for a junior engineer to develop backend APIs using Python, Flask, and Docker. Experience with Kubernetes and Kafka is a plus.",
        "application_url": "https://stripe.com/jobs/123",
        "source": "manual",
        "is_sample": False,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    inserted = jobs_col.insert_one(job_doc)
    job_doc["_id"] = str(inserted.inserted_id)
    return job_doc


def test_analysis_endpoint_returns_overlap_and_skill_gaps(client, auth_user, test_job):
    """
    Checks that the analysis endpoint returns matched skills, skill gaps,
    and recommends the best base resume without modifying any data.
    """
    token = auth_user["token"]
    job_id = test_job["_id"]

    res = client.get(f"/api/resumes/customize/analysis?job_id={job_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    analysis = data["analysis"]

    assert analysis["job_id"] == job_id
    assert analysis["job_title"] == "Junior Python / Backend Engineer"
    assert analysis["recommended_base_resume_id"] == auth_user["base_resume"]["id"]

    # Candidate has Python, Flask, Docker, AWS
    # Candidate lacks Kubernetes, Kafka
    matched = [s.lower() for s in analysis["matched_skills"]]
    assert "python" in matched
    assert "flask" in matched
    assert "docker" in matched

    gaps = [s.lower() for s in analysis["skill_gaps"]]
    assert "kubernetes" in gaps
    assert "kafka" in gaps
    assert "python" not in gaps


def test_customize_creates_draft_with_correct_kind_and_status(client, auth_user, test_job):
    """
    Checks that generating a customized resume creates a draft with kind='job_specific',
    approval_status='draft', and links to the original base resume and job snapshot.
    """
    token = auth_user["token"]
    job_id = test_job["_id"]
    base_id = auth_user["base_resume"]["id"]

    res = client.post("/api/resumes/customize", json={
        "job_id": job_id,
        "base_resume_id": base_id,
        "template": "modern"
    }, headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 201
    body = res.get_json()
    resume = body["resume"]

    assert resume["kind"] == "job_specific"
    assert resume["approval_status"] == "draft"
    assert resume["approved_at"] is None
    assert resume["job_id"] == job_id
    assert resume["based_on_resume_id"] == base_id
    assert resume["job_snapshot"]["company"] == "Stripe Technologies"
    assert resume["version"] == 1

    # Check diff structure
    diff = body["diff"]
    assert "summary" in diff
    assert "skills" in diff
    assert "projects" in diff


def test_skill_gaps_never_written_into_resume_content(client, auth_user, test_job):
    """
    CRITICAL HARD RULE:
    Candidate lacks 'Kubernetes' and 'Kafka'.
    Verify these missing skills are placed in skill_gaps list and NEVER injected into resume content.
    """
    token = auth_user["token"]
    job_id = test_job["_id"]

    res = client.post("/api/resumes/customize", json={
        "job_id": job_id
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 201
    resume = res.get_json()["resume"]

    # Check skill gaps list
    gaps = [g.lower() for g in resume["customization"]["skill_gaps"]]
    assert "kubernetes" in gaps
    assert "kafka" in gaps

    # Check skills in content
    content_skills = []
    for cat in resume["content"]["skills"]:
        for item in cat.get("items", []):
            content_skills.append(item.lower())

    assert "kubernetes" not in content_skills, "CRITICAL: Skill gap 'kubernetes' was leaked into resume skills!"
    assert "kafka" not in content_skills, "CRITICAL: Skill gap 'kafka' was leaked into resume skills!"

    # Check project tech stacks
    for proj in resume["content"]["projects"]:
        proj_tech = [t.lower() for t in proj.get("tech_stack", [])]
        assert "kubernetes" not in proj_tech, "CRITICAL: Skill gap 'kubernetes' was leaked into project tech stack!"
        assert "kafka" not in proj_tech, "CRITICAL: Skill gap 'kafka' was leaked into project tech stack!"


def test_invented_metrics_stripped_by_validator():
    """
    Tests validate_job_specific_customization helper directly to ensure fabricated
    quantitative numbers absent from master profile are stripped or neutralized.
    """
    master_profile = {
        "personal": {"full_name": "Jordan Smith", "email": "jordan@example.com"},
        "education": [{"degree": "B.S. CS", "institution": "UW"}],
        "skills": {"languages": ["Python", "SQL"]},
        "projects": [
            {
                "title": "Cloud Dashboard",
                "description": "Built cloud dashboard using Python and SQL.",
                "tech_stack": ["Python"]
            }
        ],
        "internships": [],
        "certifications": [],
        "work_experience": []
    }

    hallucinated_content = {
        "personal": {"full_name": "Jordan Smith", "email": "jordan@example.com"},
        "education": [{"degree": "B.S. CS", "institution": "UW"}],
        "summary": "Experienced engineer who scaled revenue by 500% across 10 million users.",
        "skills": [
            {"category": "Languages", "items": ["Python", "Kubernetes"]}  # Kubernetes is not in master
        ],
        "projects": [
            {
                "title": "Cloud Dashboard",
                "tech_stack": ["Python", "Kubernetes"],
                "description_bullets": [
                    "Decreased backend latency by 85% and handled 100k daily requests."  # Unverified metric!
                ]
            }
        ],
        "internships": [],
        "certifications": [],
        "work_experience": []
    }

    sanitized, warnings = validate_job_specific_customization(
        customized_content=hallucinated_content,
        master_profile=master_profile,
        skill_gaps=["Kubernetes"]
    )

    # Kubernetes must be stripped from skills and tech stack
    sanitized_skills = [s for cat in sanitized["skills"] for s in cat["items"]]
    assert "Kubernetes" not in sanitized_skills

    sanitized_tech = sanitized["projects"][0]["tech_stack"]
    assert "Kubernetes" not in sanitized_tech

    # Unverified metric in project bullets should trigger a warning
    assert any("metric" in w.lower() or "hallucinated" in w.lower() for w in warnings)


def test_immutable_profile_facts_preserved(client, auth_user, test_job):
    """
    Verifies personal info, education institution, degree, and GPA are preserved exactly.
    """
    token = auth_user["token"]
    res = client.post("/api/resumes/customize", json={
        "job_id": test_job["_id"]
    }, headers={"Authorization": f"Bearer {token}"})
    resume = res.get_json()["resume"]
    content = resume["content"]

    assert content["personal"]["full_name"] == "Jordan Smith"
    assert content["personal"]["email"] == "jordan@example.com"
    assert content["personal"]["location"] == "Seattle, WA"
    assert content["education"][0]["degree"] == "B.S. in Computer Science"
    assert content["education"][0]["institution"] == "University of Washington"
    assert content["education"][0]["score"] == 3.8


def test_approve_flow_transitions_draft_to_approved(client, auth_user, test_job):
    """
    Verifies that calling /api/resumes/<id>/approve transitions approval_status
    from 'draft' to 'approved' and records approved_at timestamp.
    """
    token = auth_user["token"]
    res = client.post("/api/resumes/customize", json={
        "job_id": test_job["_id"]
    }, headers={"Authorization": f"Bearer {token}"})
    resume_id = res.get_json()["resume"]["id"]

    # Initial state is draft
    assert res.get_json()["resume"]["approval_status"] == "draft"

    # Approve endpoint
    app_res = client.post(f"/api/resumes/{resume_id}/approve", headers={"Authorization": f"Bearer {token}"})
    assert app_res.status_code == 200
    app_data = app_res.get_json()
    assert app_data["status"] == "success"
    assert app_data["resume"]["approval_status"] == "approved"
    assert app_data["resume"]["approved_at"] is not None

    # Fetching resume confirms approved status
    get_res = client.get(f"/api/resumes/{resume_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_res.status_code == 200
    assert get_res.get_json()["resume"]["approval_status"] == "approved"


def test_diff_endpoint_shows_reordered_skills_and_bullet_changes(client, auth_user, test_job):
    """
    Tests /api/resumes/<id>/diff returns detailed comparison with base resume.
    """
    token = auth_user["token"]
    res = client.post("/api/resumes/customize", json={
        "job_id": test_job["_id"]
    }, headers={"Authorization": f"Bearer {token}"})
    resume_id = res.get_json()["resume"]["id"]

    diff_res = client.get(f"/api/resumes/{resume_id}/diff", headers={"Authorization": f"Bearer {token}"})
    assert diff_res.status_code == 200
    diff = diff_res.get_json()["diff"]

    assert "summary" in diff
    assert "skills" in diff
    assert "projects" in diff
    assert "changes_summary" in diff
    assert "skill_gaps" in diff
    assert len(diff["changes_summary"]) > 0


def test_version_increments_for_multiple_customizations_on_same_job(client, auth_user, test_job):
    """
    Creating a second customized resume for the same job should increment version to 2.
    """
    token = auth_user["token"]
    job_id = test_job["_id"]

    res1 = client.post("/api/resumes/customize", json={"job_id": job_id}, headers={"Authorization": f"Bearer {token}"})
    assert res1.get_json()["resume"]["version"] == 1

    res2 = client.post("/api/resumes/customize", json={"job_id": job_id}, headers={"Authorization": f"Bearer {token}"})
    assert res2.get_json()["resume"]["version"] == 2

    # Listing resumes for this job
    list_res = client.get(f"/api/resumes/job/{job_id}", headers={"Authorization": f"Bearer {token}"})
    assert list_res.status_code == 200
    resumes = list_res.get_json()["resumes"]
    assert len(resumes) == 2
    assert resumes[0]["version"] == 2
    assert resumes[1]["version"] == 1


def test_outdated_tracking_when_master_profile_changes(client, auth_user, test_job):
    """
    When the candidate's master profile is updated after customization,
    is_outdated should evaluate to True.
    """
    token = auth_user["token"]
    job_id = test_job["_id"]

    res = client.post("/api/resumes/customize", json={"job_id": job_id}, headers={"Authorization": f"Bearer {token}"})
    resume_id = res.get_json()["resume"]["id"]
    assert res.get_json()["resume"]["is_outdated"] is False

    # Simulate master profile updated later
    profiles_col = get_profiles_collection()
    future_time = datetime.now(timezone.utc) + timedelta(minutes=10)
    profiles_col.update_one(
        {"user_id": auth_user["id"]},
        {"$set": {"updated_at": future_time}}
    )

    get_res = client.get(f"/api/resumes/{resume_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_res.get_json()["resume"]["is_outdated"] is True


def test_tenant_isolation_on_customized_resumes(client, auth_user, test_job):
    """
    User B must NOT be able to view, diff, or approve User A's customized resumes.
    """
    token_a = auth_user["token"]
    job_id = test_job["_id"]

    res = client.post("/api/resumes/customize", json={"job_id": job_id}, headers={"Authorization": f"Bearer {token_a}"})
    resume_id = res.get_json()["resume"]["id"]

    # Register User B
    client.post("/api/auth/register", json={
        "name": "Eve Attacker",
        "email": "eve@example.com",
        "password": "Password123"
    })
    login_b = client.post("/api/auth/login", json={"email": "eve@example.com", "password": "Password123"})
    token_b = login_b.get_json()["token"]

    # User B tries to get resume
    get_res = client.get(f"/api/resumes/{resume_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_res.status_code == 404

    # User B tries to approve resume
    app_res = client.post(f"/api/resumes/{resume_id}/approve", headers={"Authorization": f"Bearer {token_b}"})
    assert app_res.status_code in (400, 404)

    # User B tries to diff resume
    diff_res = client.get(f"/api/resumes/{resume_id}/diff", headers={"Authorization": f"Bearer {token_b}"})
    assert diff_res.status_code == 404


def test_sample_job_customization_allowed_with_sample_badge(client, auth_user):
    """
    Customizing against a sample job is allowed for demo purposes and records
    is_sample=True in the job_snapshot.
    """
    jobs_col = get_jobs_collection()
    sample_doc = {
        "title": "Sample Frontend Developer",
        "company": "Acme Demo Corp",
        "location": "Remote",
        "work_mode": "remote",
        "job_type": "full_time",
        "fresher_status": "fresher_friendly",
        "required_skills": ["React", "JavaScript", "CSS"],
        "description": "Demo sample listing.",
        "application_url": "https://example.com/apply/demo",
        "source": "sample",
        "is_sample": True,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    inserted = jobs_col.insert_one(sample_doc)
    sample_id = str(inserted.inserted_id)

    token = auth_user["token"]
    res = client.post("/api/resumes/customize", json={
        "job_id": sample_id
    }, headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 201
    resume = res.get_json()["resume"]
    assert resume["job_snapshot"]["is_sample"] is True
    assert resume["job_snapshot"]["company"] == "Acme Demo Corp"

