import os
import io
import pytest
from datetime import datetime, timezone, timedelta
from bson import ObjectId

from backend.database import get_profiles_collection, get_resumes_collection


@pytest.fixture
def auth_candidate(client):
    """Creates authenticated user with a draft profile."""
    payload = {
        "name": "Jordan Smith",
        "email": "jordan@example.com",
        "password": "Password123"
    }
    client.post("/api/auth/register", json=payload)
    login_res = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = login_res.get_json()["token"]
    user_id = login_res.get_json()["user"]["id"]

    # Initialize draft master profile
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

    return {"token": token, "id": user_id, "name": payload["name"], "email": payload["email"]}


@pytest.fixture
def auth_user_other(client):
    """Creates a second authenticated user for authorization checks."""
    payload = {
        "name": "Other User",
        "email": "other@example.com",
        "password": "Password123"
    }
    client.post("/api/auth/register", json=payload)
    login_res = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = login_res.get_json()["token"]
    user_id = login_res.get_json()["user"]["id"]
    return {"token": token, "id": user_id, "name": payload["name"], "email": payload["email"]}


def test_generate_fails_if_profile_not_approved(client, auth_candidate):
    """Candidate profile is currently draft; generation must fail with 400."""
    headers = {"Authorization": f"Bearer {auth_candidate['token']}"}
    res = client.post("/api/resumes/generate", json={"target_role": "Python Developer"}, headers=headers)
    assert res.status_code == 400
    data = res.get_json()
    assert "approved" in data["message"].lower()


def test_generate_succeeds_once_profile_approved(client, auth_candidate):
    """Approve master profile, then generate a role-specific resume."""
    headers = {"Authorization": f"Bearer {auth_candidate['token']}"}

    # 1. Approve master profile
    app_res = client.post("/api/profile/approve", headers=headers)
    assert app_res.status_code == 200

    # 2. Generate resume for "Python Developer"
    gen_res = client.post(
        "/api/resumes/generate",
        json={"target_role": "Python Developer", "template": "modern"},
        headers=headers
    )
    assert gen_res.status_code == 201
    data = gen_res.get_json()
    assert data["status"] == "success"
    resume = data["resume"]

    assert resume["target_role"] == "Python Developer"
    assert resume["version"] == 1
    assert resume["template"] == "modern"
    assert resume["is_outdated"] is False
    assert len(resume["content"]["skills"]) > 0

    # Check that PDF and DOCX files were generated
    assert resume.get("pdf_path")
    assert resume.get("docx_path")
    assert os.path.exists(resume["pdf_path"])
    assert os.path.exists(resume["docx_path"])


def test_version_increments_for_same_role(client, auth_candidate):
    """Generating for the same role creates v1 then v2 without overwriting."""
    headers = {"Authorization": f"Bearer {auth_candidate['token']}"}
    client.post("/api/profile/approve", headers=headers)

    res1 = client.post("/api/resumes/generate", json={"target_role": "Full Stack Developer"}, headers=headers)
    assert res1.status_code == 201
    assert res1.get_json()["resume"]["version"] == 1

    res2 = client.post("/api/resumes/generate", json={"target_role": "Full Stack Developer"}, headers=headers)
    assert res2.status_code == 201
    assert res2.get_json()["resume"]["version"] == 2

    # Verify both versions exist
    list_res = client.get("/api/resumes", headers=headers)
    assert list_res.status_code == 200
    items = list_res.get_json()["resumes"]
    fs_resumes = [r for r in items if r["target_role"] == "Full Stack Developer"]
    assert len(fs_resumes) == 2
    versions = [r["version"] for r in fs_resumes]
    assert 1 in versions and 2 in versions


def test_batch_generate_multiple_roles(client, auth_candidate):
    """Generates multiple roles in a single request."""
    headers = {"Authorization": f"Bearer {auth_candidate['token']}"}
    client.post("/api/profile/approve", headers=headers)

    roles = ["Python Developer", "Frontend Engineer", "Data Analyst"]
    res = client.post(
        "/api/resumes/generate-multiple",
        json={"target_roles": roles, "template": "classic"},
        headers=headers
    )
    assert res.status_code == 201
    data = res.get_json()
    assert len(data["resumes"]) == 3
    for r in data["resumes"]:
        assert r["template"] == "classic"
        assert r["version"] == 1


def test_resume_marked_outdated_when_master_profile_updated(client, auth_candidate):
    """When master profile is updated later, existing resume is flagged is_outdated = True."""
    headers = {"Authorization": f"Bearer {auth_candidate['token']}"}
    client.post("/api/profile/approve", headers=headers)

    gen_res = client.post("/api/resumes/generate", json={"target_role": "Backend Developer"}, headers=headers)
    assert gen_res.status_code == 201
    resume_id = gen_res.get_json()["resume"]["id"]

    # Check initially not outdated
    one_res = client.get(f"/api/resumes/{resume_id}", headers=headers)
    assert one_res.get_json()["resume"]["is_outdated"] is False

    # Simulate master profile update in future
    profiles_col = get_profiles_collection()
    profiles_col.update_one(
        {"user_id": str(auth_candidate["id"])},
        {"$set": {"updated_at": datetime.now(timezone.utc) + timedelta(minutes=10)}}
    )

    check_res = client.get(f"/api/resumes/{resume_id}", headers=headers)
    assert check_res.get_json()["resume"]["is_outdated"] is True


def test_update_resume_and_duplicate(client, auth_candidate):
    """Updates resume content and duplicates to a new version."""
    headers = {"Authorization": f"Bearer {auth_candidate['token']}"}
    client.post("/api/profile/approve", headers=headers)

    gen_res = client.post("/api/resumes/generate", json={"target_role": "Python Developer"}, headers=headers)
    resume = gen_res.get_json()["resume"]
    resume_id = resume["id"]

    # Edit summary
    content = resume["content"]
    content["summary"] = "Customized summary by candidate with high impact."
    update_res = client.put(
        f"/api/resumes/{resume_id}",
        json={"resume_name": "My Custom Python Resume", "template": "classic", "content": content},
        headers=headers
    )
    assert update_res.status_code == 200
    updated = update_res.get_json()["resume"]
    assert updated["resume_name"] == "My Custom Python Resume"
    assert updated["template"] == "classic"
    assert updated["edited_by_user"] is True
    assert updated["content"]["summary"] == "Customized summary by candidate with high impact."

    # Duplicate resume
    dup_res = client.post(f"/api/resumes/{resume_id}/duplicate", headers=headers)
    assert dup_res.status_code == 201
    duplicated = dup_res.get_json()["resume"]
    assert duplicated["version"] == 2
    assert duplicated["content"]["summary"] == "Customized summary by candidate with high impact."


def test_download_pdf_and_docx(client, auth_candidate):
    """Downloads PDF and DOCX attachments with correct MIME types."""
    headers = {"Authorization": f"Bearer {auth_candidate['token']}"}
    client.post("/api/profile/approve", headers=headers)

    gen_res = client.post("/api/resumes/generate", json={"target_role": "QA Engineer"}, headers=headers)
    resume_id = gen_res.get_json()["resume"]["id"]

    # Download PDF
    pdf_res = client.get(f"/api/resumes/{resume_id}/download?format=pdf", headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers.get("Content-Type") == "application/pdf"
    assert len(pdf_res.data) > 0

    # Download DOCX
    docx_res = client.get(f"/api/resumes/{resume_id}/download?format=docx", headers=headers)
    assert docx_res.status_code == 200
    assert "openxmlformats-officedocument" in docx_res.headers.get("Content-Type")
    assert len(docx_res.data) > 0


def test_cross_user_isolation(client, auth_candidate, auth_user_other):
    """User B cannot access, edit, download, or delete User A's resumes."""
    headers_a = {"Authorization": f"Bearer {auth_candidate['token']}"}
    headers_b = {"Authorization": f"Bearer {auth_user_other['token']}"}

    client.post("/api/profile/approve", headers=headers_a)
    gen_res = client.post("/api/resumes/generate", json={"target_role": "Python Developer"}, headers=headers_a)
    resume_id = gen_res.get_json()["resume"]["id"]

    # User B attempts GET
    get_res = client.get(f"/api/resumes/{resume_id}", headers=headers_b)
    assert get_res.status_code == 404

    # User B attempts download
    dl_res = client.get(f"/api/resumes/{resume_id}/download?format=pdf", headers=headers_b)
    assert dl_res.status_code in [400, 404]

    # User B attempts DELETE
    del_res = client.delete(f"/api/resumes/{resume_id}", headers=headers_b)
    assert del_res.status_code == 404

