import io
import fitz
import docx
import pytest

from backend.database import get_profiles_collection
from backend.services.ai_service import clean_json_response, GeminiProvider, AIExtractionError


def create_sample_pdf(text: str = "Alex Fresh\nalex.fresh@example.com\nSoftware Engineer Fresher\nSkills: Python, React, Flask, MongoDB\nState Tech University") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_sample_docx(text: str = "Alex Fresh\nalex.fresh@example.com\nSoftware Engineer Fresher\nSkills: Python, React, Flask, MongoDB\nState Tech University") -> bytes:
    doc = docx.Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


@pytest.fixture
def auth_user_a(client):
    """Creates authenticated User A session."""
    payload = {
        "name": "User Alpha",
        "email": "alpha@example.com",
        "password": "Password123"
    }
    client.post("/api/auth/register", json=payload)
    login_res = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = login_res.get_json()["token"]
    user_id = login_res.get_json()["user"]["id"]
    return {"token": token, "id": user_id, "name": payload["name"], "email": payload["email"]}


@pytest.fixture
def auth_user_b(client):
    """Creates authenticated User B session."""
    payload = {
        "name": "User Beta",
        "email": "beta@example.com",
        "password": "Password123"
    }
    client.post("/api/auth/register", json=payload)
    login_res = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = login_res.get_json()["token"]
    user_id = login_res.get_json()["user"]["id"]
    return {"token": token, "id": user_id, "name": payload["name"], "email": payload["email"]}


def test_profile_unauthenticated_returns_401(client):
    """Verifies that accessing profile endpoints without a JWT returns 401."""
    res_get = client.get("/api/profile")
    assert res_get.status_code == 401

    res_put = client.put("/api/profile", json={})
    assert res_put.status_code == 401

    res_upload = client.post("/api/profile/upload")
    assert res_upload.status_code == 401

    res_approve = client.post("/api/profile/approve")
    assert res_approve.status_code == 401

    res_delete = client.delete("/api/profile")
    assert res_delete.status_code == 401


def test_get_empty_profile_for_new_user(client, auth_user_a):
    """Verifies that a new candidate gets an initialized profile skeleton with registered details."""
    headers = {"Authorization": f"Bearer {auth_user_a['token']}"}
    response = client.get("/api/profile", headers=headers)
    assert response.status_code == 200

    data = response.get_json()
    assert "profile" in data
    profile = data["profile"]
    assert profile["personal"]["full_name"] == auth_user_a["name"]
    assert profile["personal"]["email"] == auth_user_a["email"]
    assert profile["profile_status"] == "draft"
    assert isinstance(profile["skills"]["languages"], list)
    assert isinstance(profile["education"], list)


def test_save_and_update_profile(client, auth_user_a):
    """Verifies saving and updating profile data with validation and completeness calculation."""
    headers = {"Authorization": f"Bearer {auth_user_a['token']}"}

    profile_payload = {
        "personal": {
            "full_name": "Alpha Candidate",
            "email": auth_user_a["email"],
            "phone": "+1-555-0123",
            "location": "New York, NY",
            "linkedin_url": "https://linkedin.com/in/alphacand",
            "github_url": "https://github.com/alphacand"
        },
        "education": [
            {
                "degree": "B.S. in Computer Science",
                "institution": "Tech University",
                "graduation_year": 2024,
                "score_type": "cgpa",
                "score": 9.2
            }
        ],
        "skills": {
            "languages": ["Python", "JavaScript", "SQL"],
            "frameworks": ["React", "Flask"],
            "databases": ["MongoDB"],
            "tools": ["Git", "Docker"],
            "other": ["Agile"]
        },
        "projects": [
            {
                "title": "Job Matcher AI",
                "description": "Matches resumes to job specs.",
                "tech_stack": ["Python", "React"],
                "link": "https://github.com/alphacand/job-matcher"
            }
        ],
        "internships": [
            {
                "company": "Startup Co",
                "role": "Frontend Intern",
                "start_date": "Jun 2023",
                "end_date": "Aug 2023",
                "description": "Built user interfaces."
            }
        ],
        "certifications": [
            {
                "name": "AWS Certified Cloud Practitioner",
                "issuer": "Amazon Web Services",
                "year": 2023
            }
        ],
        "achievements": ["Hackathon Winner 2023"],
        "work_experience": [],
        "preferred_roles": ["Frontend Engineer", "Full Stack Developer"],
        "preferred_locations": ["Remote", "New York, NY"],
        "profile_status": "draft"
    }

    # 1. Save profile
    save_res = client.put("/api/profile", headers=headers, json=profile_payload)
    assert save_res.status_code == 200
    saved = save_res.get_json()["profile"]
    assert saved["personal"]["full_name"] == "Alpha Candidate"
    assert saved["education"][0]["score"] == 9.2
    assert saved["completeness"] >= 80

    # 2. Retrieve profile via GET
    get_res = client.get("/api/profile", headers=headers)
    assert get_res.status_code == 200
    retrieved = get_res.get_json()["profile"]
    assert retrieved["personal"]["phone"] == "+1-555-0123"
    assert len(retrieved["skills"]["languages"]) == 3


def test_reject_invalid_cgpa_and_percentage(client, auth_user_a):
    """Verifies that CGPA > 10.0 or percentage > 100.0 is rejected with HTTP 400."""
    headers = {"Authorization": f"Bearer {auth_user_a['token']}"}

    # Invalid CGPA: 11.5
    invalid_cgpa_payload = {
        "education": [
            {
                "degree": "B.Tech",
                "institution": "College",
                "score_type": "cgpa",
                "score": 11.5
            }
        ]
    }
    res_cgpa = client.put("/api/profile", headers=headers, json=invalid_cgpa_payload)
    assert res_cgpa.status_code == 400

    # Invalid percentage: 105.0
    invalid_pct_payload = {
        "education": [
            {
                "degree": "B.Tech",
                "institution": "College",
                "score_type": "percentage",
                "score": 105.0
            }
        ]
    }
    res_pct = client.put("/api/profile", headers=headers, json=invalid_pct_payload)
    assert res_pct.status_code == 400


def test_upload_resume_pdf_extraction_without_saving(client, auth_user_a):
    """
    Verifies that uploading a valid PDF parses text, runs AI extraction (in mock mode),
    and returns structured data WITHOUT saving to database.
    """
    headers = {"Authorization": f"Bearer {auth_user_a['token']}"}
    pdf_bytes = create_sample_pdf("Alex Fresh\nPython React Developer\nState Tech University\nGraduation 2024")

    data = {
        "resume": (io.BytesIO(pdf_bytes), "sample_resume.pdf", "application/pdf")
    }

    upload_res = client.post(
        "/api/profile/upload",
        headers=headers,
        data=data,
        content_type="multipart/form-data"
    )
    assert upload_res.status_code == 200
    res_json = upload_res.get_json()
    assert "extracted_data" in res_json
    extracted = res_json["extracted_data"]
    assert "personal" in extracted
    assert "education" in extracted
    assert "skills" in extracted

    # CRITICAL: Verify data was NOT saved directly to database
    get_res = client.get("/api/profile", headers=headers)
    db_profile = get_res.get_json()["profile"]
    assert db_profile["profile_status"] == "draft"


def test_upload_resume_docx_extraction(client, auth_user_a):
    """Verifies that uploading a valid DOCX file succeeds and returns structured profile."""
    headers = {"Authorization": f"Bearer {auth_user_a['token']}"}
    docx_bytes = create_sample_docx("Alex Fresh\nPython React Developer\nState Tech University\nGraduation 2024")

    data = {
        "resume": (io.BytesIO(docx_bytes), "resume.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    }

    upload_res = client.post(
        "/api/profile/upload",
        headers=headers,
        data=data,
        content_type="multipart/form-data"
    )
    assert upload_res.status_code == 200
    assert "extracted_data" in upload_res.get_json()


def test_upload_rejects_spoofed_file(client, auth_user_a):
    """Verifies that an executable renamed as .pdf is rejected by magic bytes inspection."""
    headers = {"Authorization": f"Bearer {auth_user_a['token']}"}
    spoofed_bytes = b"MZ\x90\x00\x03\x00\x00\x00FakeBinary"

    data = {
        "resume": (io.BytesIO(spoofed_bytes), "trojan.pdf", "application/pdf")
    }

    upload_res = client.post(
        "/api/profile/upload",
        headers=headers,
        data=data,
        content_type="multipart/form-data"
    )
    assert upload_res.status_code == 400
    assert "not a valid PDF" in upload_res.get_json()["error"]


def test_upload_rejects_empty_scanned_pdf(client, auth_user_a):
    """Verifies that a blank or scanned PDF produces a friendly error."""
    headers = {"Authorization": f"Bearer {auth_user_a['token']}"}
    doc = fitz.open()
    doc.new_page()
    empty_pdf = doc.tobytes()
    doc.close()

    data = {
        "resume": (io.BytesIO(empty_pdf), "scanned.pdf", "application/pdf")
    }

    upload_res = client.post(
        "/api/profile/upload",
        headers=headers,
        data=data,
        content_type="multipart/form-data"
    )
    assert upload_res.status_code == 400
    assert "Could not extract text" in upload_res.get_json()["error"]


def test_approve_profile_flow(client, auth_user_a):
    """Verifies approving a profile updates profile_status to 'approved'."""
    headers = {"Authorization": f"Bearer {auth_user_a['token']}"}

    # 1. Save profile
    client.put("/api/profile", headers=headers, json={
        "personal": {"full_name": auth_user_a["name"], "email": auth_user_a["email"]}
    })

    # 2. Approve profile
    approve_res = client.post("/api/profile/approve", headers=headers)
    assert approve_res.status_code == 200
    assert approve_res.get_json()["profile"]["profile_status"] == "approved"

    # 3. Verify GET reflects approved status
    get_res = client.get("/api/profile", headers=headers)
    assert get_res.get_json()["profile"]["profile_status"] == "approved"


def test_delete_profile_flow(client, auth_user_a):
    """Verifies that user-controlled profile deletion removes document."""
    headers = {"Authorization": f"Bearer {auth_user_a['token']}"}

    # Save
    client.put("/api/profile", headers=headers, json={
        "personal": {"full_name": "To Be Deleted", "email": auth_user_a["email"]}
    })

    # Delete
    del_res = client.delete("/api/profile", headers=headers)
    assert del_res.status_code == 200
    assert del_res.get_json()["deleted"] is True

    # Next GET should return fresh empty skeleton
    get_res = client.get("/api/profile", headers=headers)
    assert get_res.get_json()["profile"]["profile_status"] == "draft"


def test_tenant_isolation_user_a_cannot_access_or_modify_user_b(client, auth_user_a, auth_user_b):
    """
    Verifies strict tenant isolation:
    User A's profile operations never touch or expose User B's profile.
    """
    headers_a = {"Authorization": f"Bearer {auth_user_a['token']}"}
    headers_b = {"Authorization": f"Bearer {auth_user_b['token']}"}

    # User A creates their profile
    client.put("/api/profile", headers=headers_a, json={
        "personal": {"full_name": "Secret Profile A", "email": auth_user_a["email"]}
    })

    # User B creates their profile
    client.put("/api/profile", headers=headers_b, json={
        "personal": {"full_name": "Secret Profile B", "email": auth_user_b["email"]}
    })

    # User A reads profile -> receives ONLY Profile A
    get_a = client.get("/api/profile", headers=headers_a)
    assert get_a.get_json()["profile"]["personal"]["full_name"] == "Secret Profile A"

    # User B reads profile -> receives ONLY Profile B
    get_b = client.get("/api/profile", headers=headers_b)
    assert get_b.get_json()["profile"]["personal"]["full_name"] == "Secret Profile B"

    # User A deletes profile -> User B's profile remains intact
    client.delete("/api/profile", headers=headers_a)
    get_b_again = client.get("/api/profile", headers=headers_b)
    assert get_b_again.get_json()["profile"]["personal"]["full_name"] == "Secret Profile B"


def test_ai_clean_json_helper():
    """Verifies markdown fence stripping from raw LLM responses."""
    fenced = "```json\n{\"personal\": {\"full_name\": \"Test\"}}\n```"
    assert clean_json_response(fenced) == "{\"personal\": {\"full_name\": \"Test\"}}"


def test_ai_malformed_json_retry_and_error(monkeypatch):
    """Verifies that malformed LLM output triggers a retry and raises AIExtractionError if retry fails."""
    provider = GeminiProvider(api_key="fake-test-key")

    call_count = 0

    class FakeModels:
        def generate_content(self, model, contents):
            nonlocal call_count
            call_count += 1
            class Response:
                text = "This is not valid JSON at all"
            return Response()

    class FakeClient:
        def __init__(self, api_key):
            self.models = FakeModels()

    import google.genai
    monkeypatch.setattr(google.genai, "Client", FakeClient)

    with pytest.raises(AIExtractionError) as exc_info:
        provider.extract_profile_data("sample text")

    # Confirms 1 initial call + 1 retry = 2 calls before raising friendly error
    assert call_count == 2
    assert "AI failed to generate valid profile JSON after retry" in str(exc_info.value)

