import pytest
from datetime import datetime, timezone, timedelta

from backend.services.job_sources.sample_source import SampleJobSource
from backend.services.job_sources.api_source_example import AdzunaJobSource
from backend.services.job_normalizer import (
    parse_experience,
    classify_fresher_status,
    sanitize_text,
    normalize_job_dict
)
from backend.services.dedup_service import (
    detect_and_link_duplicates,
    apply_expiration_check,
    is_job_expired
)
from backend.database import get_jobs_collection, get_saved_jobs_collection


@pytest.fixture
def auth_candidate(client):
    """Creates authenticated User A session."""
    payload = {
        "name": "Alex Fresher",
        "email": "alex.discovery@example.com",
        "password": "Password123"
    }
    client.post("/api/auth/register", json=payload)
    login_res = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = login_res.get_json()["token"]
    user_id = login_res.get_json()["user"]["id"]
    return {"token": token, "id": user_id, "name": payload["name"], "email": payload["email"]}


@pytest.fixture
def auth_candidate_b(client):
    """Creates authenticated User B session."""
    payload = {
        "name": "Jordan Candidate",
        "email": "jordan.other@example.com",
        "password": "Password123"
    }
    client.post("/api/auth/register", json=payload)
    login_res = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = login_res.get_json()["token"]
    user_id = login_res.get_json()["user"]["id"]
    return {"token": token, "id": user_id, "name": payload["name"], "email": payload["email"]}


def test_sample_source_returns_sample_jobs():
    """Sample source loads realistic listings all explicitly tagged is_sample=True."""
    source = SampleJobSource()
    assert source.is_enabled is True
    jobs = source.fetch_jobs(limit=10)
    assert len(jobs) > 0
    for j in jobs:
        assert j["is_sample"] is True
        assert j["source"] == "sample"
        assert j["application_url"].startswith("http")
        assert "example.com" in j["application_url"]


def test_normalizer_experience_parsing():
    """Parses various experience strings into numeric min and max years."""
    # 0-1 years
    min_y, max_y = parse_experience("0-1 years")
    assert min_y == 0.0 and max_y == 1.0

    # Freshers / graduate
    min_y, max_y = parse_experience("Freshers welcome (2024 batch)")
    assert min_y == 0.0 and max_y == 0.0

    # 3-5 years
    min_y, max_y = parse_experience("3-5 years")
    assert min_y == 3.0 and max_y == 5.0

    # 2+ years
    min_y, max_y = parse_experience("2+ years experience")
    assert min_y == 2.0 and max_y is None

    # Unclear
    min_y, max_y = parse_experience("Competitive experience")
    assert min_y is None and max_y is None


def test_normalizer_fresher_status_classification():
    """Classifies jobs deterministically into appropriate fresher status."""
    # 5 years -> experience_required
    assert classify_fresher_status("Software Engineer", "5 years", 5.0, 5.0) == "experience_required"

    # Senior in title -> experience_required
    assert classify_fresher_status("Senior Backend Lead", "1-2 years", 1.0, 2.0) == "experience_required"

    # 0-1 years -> fresher_friendly
    assert classify_fresher_status("Junior Python Dev", "0-1 years", 0.0, 1.0) == "fresher_friendly"

    # 1-2 years -> entry_level
    assert classify_fresher_status("Associate Developer", "1-2 years", 1.0, 2.0) == "entry_level"

    # Ambiguous text -> unclear
    assert classify_fresher_status("Programmer", "Competitive", None, None) == "unclear"


def test_normalizer_security_sanitization():
    """Strips HTML tags, clamps length, and validates application_url."""
    raw = {
        "job_id": "test-sec-1",
        "title": "<b>Junior Dev</b><script>alert('xss')</script>",
        "company": "SecureCorp",
        "location": "Bengaluru",
        "description": "<p>Hello <b>world</b>! <script>evil()</script></p>" + ("A" * 6000),
        "application_url": "javascript:alert(1)" # Invalid scheme
    }
    norm = normalize_job_dict(raw)
    assert "<script>" not in norm["title"]
    assert "alert('xss')" in norm["title"]
    assert "<p>" not in norm["description"]
    assert len(norm["description"]) <= 5000
    assert norm["application_url"].startswith("http")


def test_deduplication_engine():
    """Merges obvious duplicates with duplicate_group_id and keeps distinct jobs separate."""
    job1 = {
        "job_id": "j1",
        "title": "Junior Python Developer",
        "normalized_title": "junior python developer",
        "company": "Apex Analytics",
        "location": "Bengaluru",
        "work_mode": "hybrid"
    }
    job2 = {
        "job_id": "j2",
        "title": "Junior Python Backend Developer",
        "normalized_title": "junior python backend developer",
        "company": "Apex Analytics",
        "location": "Bengaluru",
        "work_mode": "hybrid"
    }
    job3 = {
        "job_id": "j3",
        "title": "React Frontend Developer",
        "normalized_title": "react frontend developer",
        "company": "Apex Analytics",
        "location": "Bengaluru",
        "work_mode": "hybrid"
    }

    processed, dup_count = detect_and_link_duplicates([job1, job2, job3])
    assert dup_count == 1
    assert processed[0]["duplicate_group_id"] is None
    assert processed[1]["duplicate_group_id"] == "j1"
    assert processed[2]["duplicate_group_id"] is None


def test_expiration_engine():
    """Detects expired jobs past deadline or older than 45 days."""
    now = datetime.now(timezone.utc)

    job_active = {
        "job_id": "act",
        "posted_at": now - timedelta(days=5),
        "deadline": now + timedelta(days=20),
        "status": "active"
    }
    job_past_deadline = {
        "job_id": "exp1",
        "posted_at": now - timedelta(days=10),
        "deadline": now - timedelta(days=1),
        "status": "active"
    }
    job_stale = {
        "job_id": "exp2",
        "posted_at": now - timedelta(days=60),
        "deadline": None,
        "status": "active"
    }

    assert is_job_expired(job_active) is False
    assert is_job_expired(job_past_deadline) is True
    assert is_job_expired(job_stale) is True

    processed, exp_count = apply_expiration_check([job_active, job_past_deadline, job_stale])
    assert exp_count == 2
    assert processed[0]["status"] == "active"
    assert processed[1]["status"] == "expired"
    assert processed[2]["status"] == "expired"


def test_discover_and_filtering_endpoints(client, auth_candidate):
    """Runs discovery endpoint, verifies summary, and tests query filters."""
    headers = {"Authorization": f"Bearer {auth_candidate['token']}"}

    # 1. Run discovery
    disc_res = client.post("/api/jobs/discover", json={}, headers=headers)
    assert disc_res.status_code == 200
    summary = disc_res.get_json()["summary"]
    assert summary["stored"] > 0
    assert summary["duplicates_flagged"] >= 1
    assert summary["expired_flagged"] >= 1

    # 2. Get jobs feed (default excludes expired and secondary duplicates)
    feed_res = client.get("/api/jobs", headers=headers)
    assert feed_res.status_code == 200
    data = feed_res.get_json()
    assert len(data["jobs"]) > 0

    # 3. Filter fresher_only=true
    fresh_res = client.get("/api/jobs?fresher_only=true", headers=headers)
    assert fresh_res.status_code == 200
    for j in fresh_res.get_json()["jobs"]:
        assert j["fresher_status"] in ["fresher_friendly", "entry_level"]

    # 4. Filter work_mode=remote
    remote_res = client.get("/api/jobs?work_mode=remote", headers=headers)
    assert remote_res.status_code == 200
    for j in remote_res.get_json()["jobs"]:
        assert j["work_mode"] == "remote"


def test_saved_jobs_lifecycle_and_isolation(client, auth_candidate, auth_candidate_b):
    """Candidate can save/unsave jobs; saved list is strictly isolated per candidate."""
    headers_a = {"Authorization": f"Bearer {auth_candidate['token']}"}
    headers_b = {"Authorization": f"Bearer {auth_candidate_b['token']}"}

    # Discover jobs
    client.post("/api/jobs/discover", json={}, headers=headers_a)
    jobs_res = client.get("/api/jobs", headers=headers_a)
    job_id = jobs_res.get_json()["jobs"][0]["job_id"]

    # User A saves job
    save_res = client.post(f"/api/jobs/{job_id}/save", json={"notes": "High priority backend role"}, headers=headers_a)
    assert save_res.status_code == 200

    # User A verifies it is saved
    saved_a = client.get("/api/jobs/saved", headers=headers_a)
    assert saved_a.status_code == 200
    assert len(saved_a.get_json()["saved_jobs"]) == 1
    assert saved_a.get_json()["saved_jobs"][0]["job_id"] == job_id
    assert saved_a.get_json()["saved_jobs"][0]["saved_notes"] == "High priority backend role"

    # User B should NOT see User A's saved job (isolation)
    saved_b = client.get("/api/jobs/saved", headers=headers_b)
    assert saved_b.status_code == 200
    assert len(saved_b.get_json()["saved_jobs"]) == 0

    # User A unsaves job
    unsave_res = client.delete(f"/api/jobs/{job_id}/save", headers=headers_a)
    assert unsave_res.status_code == 200

    # Verify list is empty for User A
    saved_a2 = client.get("/api/jobs/saved", headers=headers_a)
    assert len(saved_a2.get_json()["saved_jobs"]) == 0


def test_adzuna_adapter_disabled_gracefully_when_keys_missing():
    """Verifies that missing Adzuna credentials gracefully disable the adapter without errors."""
    adzuna = AdzunaJobSource()
    if not (adzuna.is_enabled):
        # When unconfigured, fetch_jobs safely returns empty list
        assert adzuna.fetch_jobs() == []


def test_unauthenticated_requests_return_401(client):
    """Endpoints require valid authentication."""
    assert client.get("/api/jobs").status_code == 401
    assert client.post("/api/jobs/discover").status_code == 401
    assert client.get("/api/jobs/saved").status_code == 401
    assert client.put("/api/jobs/preferences").status_code == 401

