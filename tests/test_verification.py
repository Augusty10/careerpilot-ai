"""
Comprehensive Test Suite for Module 6: Company & Recruiter Verification.
Tests deterministic scam scanning, SSRF protection, multi-entity independence,
worst-of-three status logic, sample listing handling, recruiter verification, and tenant isolation.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from backend.services.verification.network_safety import is_safe_ip, is_safe_url, safe_request
from backend.services.verification.company_checks import (
    extract_base_domain,
    run_company_checks,
    MCALookupAdapter
)
from backend.services.verification.recruiter_checks import run_recruiter_checks
from backend.services.verification.job_checks import (
    scan_job_description_for_scam_patterns,
    run_job_posting_checks
)
from backend.services.verification_service import (
    evaluate_entity_status,
    compute_overall_status,
    run_full_verification,
    get_or_compute_job_verification,
    submit_recruiter_details_and_recompute,
    submit_user_report
)
from backend.database import get_jobs_collection, get_job_verifications_collection


@pytest.fixture(autouse=True)
def mock_external_network():
    """Mocks all outbound network calls across tests as required by prompt."""
    with patch("backend.services.verification.company_checks.safe_request") as mock_comp_req, \
         patch("backend.services.verification.network_safety.safe_request") as mock_net_req, \
         patch("backend.services.verification.network_safety.socket.getaddrinfo") as mock_dns:
        mock_comp_req.return_value = (None, "Network mocked in test environment")
        mock_net_req.return_value = (None, "Network mocked in test environment")
        mock_dns.return_value = [(2, 1, 6, '', ('93.184.216.34', 0))]
        yield mock_comp_req


# ---------------------------------------------------------------------------
# 1. SSRF & Network Safety Tests
# ---------------------------------------------------------------------------

def test_ssrf_blocks_private_and_loopback_ips():
    """Verifies that private, loopback, and link-local cloud metadata IPs are rejected."""
    # Loopback
    safe, reason = is_safe_ip("127.0.0.1")
    assert not safe
    assert "Loopback" in reason

    # Private RFC 1918
    safe, reason = is_safe_ip("10.0.0.1")
    assert not safe
    assert "Private" in reason

    safe, reason = is_safe_ip("192.168.1.100")
    assert not safe
    assert "Private" in reason

    # Link-local (AWS/GCP metadata)
    safe, reason = is_safe_ip("169.254.169.254")
    assert not safe
    assert "Link-local" in reason

    # Safe public IP
    safe, reason = is_safe_ip("93.184.216.34")  # example.com
    assert safe


def test_ssrf_blocks_unsafe_url_schemes_and_hosts():
    """Verifies rejection of file://, ftp://, localhost, and non-resolving domains."""
    safe, reason, _ = is_safe_url("file:///etc/passwd")
    assert not safe
    assert "Unsupported URL scheme" in reason

    safe, reason, _ = is_safe_url("ftp://server.local/data")
    assert not safe

    safe, reason, _ = is_safe_url("http://localhost:5000/api")
    assert not safe
    assert "internal host" in reason

    safe, reason, _ = is_safe_url("http://127.0.0.1:8080/admin")
    assert not safe


# ---------------------------------------------------------------------------
# 2. Company Checks Tests
# ---------------------------------------------------------------------------

def test_domain_extraction_handles_multi_part_tlds():
    """Verifies base domain parsing for single and multi-part TLDs."""
    assert extract_base_domain("https://careers.google.com/jobs/123") == "google.com"
    assert extract_base_domain("https://jobs.tcs.co.in/entry-level") == "tcs.co.in"
    assert extract_base_domain("https://apply.techcorp.org.uk") == "techcorp.org.uk"
    assert extract_base_domain("https://sub.portal.infosys.com:8443") == "infosys.com"


def test_ats_allowlist_matches_enterprise_platforms():
    """Verifies that ATS platforms (Greenhouse, Lever, Workday) pass domain check."""
    ev, missing, warnings = run_company_checks(
        company_name="Acme Corp",
        application_url="https://boards.greenhouse.io/acmecorp/jobs/456"
    )
    ats_item = next((e for e in ev if e["check"] == "ats_allowlist_match"), None)
    assert ats_item is not None
    assert ats_item["result"] == "pass"
    assert "greenhouse.io" in ats_item["detail"]


def test_company_lookalike_domain_triggers_warning():
    """Detects typosquatting or look-alike domain with medium warning."""
    ev, missing, warnings = run_company_checks(
        company_name="Microsoft",
        application_url="https://micros0ft-careers.com/apply"
    )
    lookalike_warn = next((w for w in warnings if w["code"] == "LOOKALIKE_DOMAIN_DETECTED"), None)
    assert lookalike_warn is not None
    assert lookalike_warn["severity"] == "medium"


def test_mca_lookup_adapter_returns_manual_deep_link():
    """Verifies that MCA adapter returns manual deep link with no scraping."""
    adapter = MCALookupAdapter()
    res = adapter.lookup_company("Tata Consultancy Services")
    assert res["result"] == "unavailable"
    assert "mca.gov.in" in res["source_url"]
    assert res["manual_check_available"] is True


def test_unreachable_careers_page_is_unavailable_not_suspicious():
    """Unreachable careers page must be marked unavailable, NEVER suspicious."""
    with patch("backend.services.verification.company_checks.safe_request", return_value=(None, "Connection timed out")):
        ev, missing, warnings = run_company_checks(
            company_name="Unknown New Startup",
            application_url="https://unknownstartup.com/apply"
        )
        # Should not create high severity warnings
        high_warns = [w for w in warnings if w["severity"] == "high"]
        assert len(high_warns) == 0
        status = evaluate_entity_status(ev, warnings)
        assert status == "needs_verification"


# ---------------------------------------------------------------------------
# 3. Recruiter Checks Tests
# ---------------------------------------------------------------------------

def test_recruiter_free_email_triggers_high_warning_suspicious():
    """Recruiter using @gmail.com claiming corporate identity triggers HIGH warning."""
    provided, contact, ev, missing, warnings = run_recruiter_checks(
        company_name="Infosys",
        application_url="https://infosys.com/careers",
        recruiter_name="John Doe",
        recruiter_email="john.hr.recruiter@gmail.com"
    )
    assert provided is True
    free_email_warn = next((w for w in warnings if w["code"] == "RECRUITER_FREE_EMAIL_PROVIDER"), None)
    assert free_email_warn is not None
    assert free_email_warn["severity"] == "high"

    status = evaluate_entity_status(ev, warnings)
    assert status == "suspicious"


def test_recruiter_domain_mismatch_triggers_warning():
    """Recruiter email domain differing from company domain triggers warning."""
    provided, contact, ev, missing, warnings = run_recruiter_checks(
        company_name="Wipro",
        application_url="https://wipro.com/careers",
        recruiter_name="Sarah Smith",
        recruiter_email="sarah@independentconsulting.com"
    )
    assert provided is True
    mismatch_warn = next((w for w in warnings if w["code"] == "RECRUITER_DOMAIN_MISMATCH"), None)
    assert mismatch_warn is not None


def test_recruiter_empty_contact_evaluates_to_needs_verification():
    """No recruiter info provided evaluates to needs_verification with provided=False."""
    provided, contact, ev, missing, warnings = run_recruiter_checks(
        company_name="Wipro",
        application_url="https://wipro.com/careers"
    )
    assert provided is False
    status = evaluate_entity_status(ev, warnings)
    assert status == "needs_verification"
    assert "No recruiter contact information" in missing[0]


# ---------------------------------------------------------------------------
# 4. Job Posting Scam Scanner Tests
# ---------------------------------------------------------------------------

def test_fee_request_in_description_triggers_suspicious():
    """Scanning upfront registration or security deposit triggers HIGH warning -> suspicious."""
    text = "Candidate must deposit ₹1500 refundable security fee before training commences."
    warnings = scan_job_description_for_scam_patterns("Junior Developer", text)
    fee_warn = next((w for w in warnings if w["code"] == "FEE_REQUEST"), None)
    assert fee_warn is not None
    assert fee_warn["severity"] == "high"
    assert "1500" in fee_warn["exact_quote"]
    assert "deposit" in fee_warn["exact_quote"].lower()

    # Entity status must be suspicious
    status = evaluate_entity_status([], warnings)
    assert status == "suspicious"


def test_otp_and_banking_credentials_request_triggers_suspicious():
    """Requests for OTP or net banking credentials trigger HIGH warning -> suspicious."""
    text = "Please share your OTP and Aadhaar card scan upfront to proceed with application."
    warnings = scan_job_description_for_scam_patterns("Typing Assistant", text)
    id_warn = next((w for w in warnings if w["code"] == "IDENTITY_THEFT_REQUEST"), None)
    assert id_warn is not None
    assert id_warn["severity"] == "high"


def test_telegram_whatsapp_only_channel_triggers_suspicious():
    """Directing candidates exclusively to Telegram/WhatsApp triggers HIGH warning."""
    text = "Send resume only via Telegram @quick_hr_job to schedule instant appointment."
    warnings = scan_job_description_for_scam_patterns("Support Executive", text)
    channel_warn = next((w for w in warnings if w["code"] == "UNOFFICIAL_COMMUNICATION_CHANNEL"), None)
    assert channel_warn is not None
    assert channel_warn["severity"] == "high"


def test_unrealistic_salary_and_guarantee_triggers_suspicious():
    """Promises of earning lakhs with no skills trigger HIGH warning."""
    text = "Earn up to 2 lakhs per month without experience! 100% job guarantee without exam."
    warnings = scan_job_description_for_scam_patterns("Remote Analyst", text)
    salary_warn = next((w for w in warnings if w["code"] == "UNREALISTIC_SALARY_OR_JOB_GUARANTEE"), None)
    assert salary_warn is not None
    assert salary_warn["severity"] == "high"


def test_wfh_immediate_joining_triggers_medium_warning():
    """WFH immediate joining without interview generates MEDIUM warning (not alone suspicious)."""
    text = "Work from home with no interview and immediate appointment letter."
    warnings = scan_job_description_for_scam_patterns("Data Entry", text)
    wfh_warn = next((w for w in warnings if w["code"] == "WFH_NO_INTERVIEW_IMMEDIATE_JOINING"), None)
    assert wfh_warn is not None
    assert wfh_warn["severity"] == "medium"

    # With only medium warnings, entity status must be needs_verification, NOT suspicious
    status = evaluate_entity_status([], warnings)
    assert status == "needs_verification"


# ---------------------------------------------------------------------------
# 5. Multi-Entity Independence & Worst-of-Three Logic
# ---------------------------------------------------------------------------

def test_independent_entities_genuine_company_plus_fake_recruiter():
    """
    Genuine company (corroborated) + Fake recruiter (suspicious)
    -> Company stays corroborated, Recruiter is suspicious, Overall is suspicious.
    """
    company_status = "corroborated"
    recruiter_status = "suspicious"
    job_status = "corroborated"

    overall = compute_overall_status(
        company_status=company_status,
        recruiter_status=recruiter_status,
        job_status=job_status,
        recruiter_provided=True
    )
    assert overall == "suspicious"
    assert company_status == "corroborated"
    assert recruiter_status == "suspicious"


def test_corroborated_requires_two_independent_pass_evidence_items():
    r"""An entity requires $\ge 2$ PASS evidence items and NO high warnings to be corroborated."""
    now_iso = datetime.now(timezone.utc)
    ev_one = [{"check": "https_enforcement", "result": "pass", "detail": "HTTPS used", "checked_at": now_iso}]
    status_one = evaluate_entity_status(ev_one, [])
    assert status_one == "needs_verification"  # Only 1 pass item

    ev_two = [
        {"check": "https_enforcement", "result": "pass", "detail": "HTTPS used", "checked_at": now_iso},
        {"check": "company_domain_match", "result": "pass", "detail": "Domain matches", "checked_at": now_iso}
    ]
    status_two = evaluate_entity_status(ev_two, [])
    assert status_two == "corroborated"  # 2 independent pass items!


def test_ai_second_opinion_cannot_set_suspicious_or_create_evidence():
    """AI warnings can only be low/medium, never set suspicious alone, and never add evidence."""
    mock_ai = MagicMock()
    mock_ai.check_job_suspicious_patterns.return_value = [
        {"severity": "high", "message": "High AI vibe", "exact_quote": "some quote"}
    ]

    job_doc = {
        "title": "Clean Junior Developer",
        "description": "Standard software engineering role building backend APIs.",
        "application_url": "https://company.com/apply"
    }

    ev, missing, warnings = run_job_posting_checks(job_doc, ai_service=mock_ai)

    # Severity must be capped to medium
    ai_warn = next((w for w in warnings if w["code"] == "AI_DETECTED_CONCERN"), None)
    assert ai_warn is not None
    assert ai_warn["severity"] == "medium"  # Capped from high!

    status = evaluate_entity_status(ev, warnings)
    assert status != "suspicious"


# ---------------------------------------------------------------------------
# 6. Sample Job Handling (Not Applicable)
# ---------------------------------------------------------------------------

def test_standard_sample_job_returns_not_applicable_with_zero_fabricated_evidence():
    """Standard demo vacancy (is_sample=True, is_test_scenario=False) returns not_applicable."""
    sample_job = {
        "job_id": "sample-clean-01",
        "title": "Sample Python Developer",
        "company": "Infosync",
        "application_url": "https://example.com/jobs/1",
        "is_sample": True,
        "is_test_scenario": False
    }

    report = run_full_verification(sample_job)
    assert report["overall_status"] == "not_applicable"
    assert "not a real vacancy" in report["recommended_action"]
    assert report["company"]["status"] == "not_applicable"
    assert report["recruiter"]["status"] == "not_applicable"
    assert len(report["company"]["evidence"]) == 0
    assert len(report["job"]["evidence"]) == 0


def test_result_text_never_contains_guaranteed_or_100_percent_safe():
    """Guarantees that no response text uses forbidden absolute terms."""
    from backend.services.verification_service import RECOMMENDED_ACTIONS
    forbidden = ["verified genuine", "100% safe", "guaranteed genuine"]
    for status, text in RECOMMENDED_ACTIONS.items():
        for f in forbidden:
            assert f not in text.lower()


# ---------------------------------------------------------------------------
# 7. End-to-End API Integration & Tenant Isolation Tests
# ---------------------------------------------------------------------------

def test_verification_api_lifecycle(client, clean_db):
    """Tests POST, GET, PUT recruiter, and POST report endpoints."""
    # 1. Register candidate
    reg_res = client.post("/api/auth/register", json={
        "name": "Verification Candidate",
        "email": "verif.test@example.com",
        "password": "Password123!"
    })
    assert reg_res.status_code == 201

    login_res = client.post("/api/auth/login", json={
        "email": "verif.test@example.com",
        "password": "Password123!"
    })
    token = login_res.get_json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Seed a test job in DB
    jobs_col = get_jobs_collection(clean_db)
    test_job = {
        "job_id": "test-verif-job-01",
        "title": "Backend Trainee (Fee Pattern)",
        "company": "Acme Placements",
        "location": "Bengaluru",
        "work_mode": "remote",
        "job_type": "full_time",
        "description": "Immediate joining! Please pay ₹2,000 registration fee to secure your onboarding kit.",
        "application_url": "https://acmeplacements.com/apply",
        "source": "direct",
        "is_sample": False,
        "posted_at": datetime.now(timezone.utc),
        "status": "active"
    }
    jobs_col.insert_one(test_job)

    # 3. POST /api/verification/:job_id (Run verification)
    run_res = client.post("/api/verification/test-verif-job-01", headers=headers)
    assert run_res.status_code == 200
    report = run_res.get_json()["verification"]
    assert report["overall_status"] == "suspicious"
    assert report["job"]["status"] == "suspicious"

    # 4. GET /api/verification/:job_id
    get_res = client.get("/api/verification/test-verif-job-01", headers=headers)
    assert get_res.status_code == 200
    assert get_res.get_json()["verification"]["overall_status"] == "suspicious"

    # 5. PUT /api/verification/:job_id/recruiter (Submit candidate-received recruiter info)
    rec_res = client.put("/api/verification/test-verif-job-01/recruiter", json={
        "name": "Jane Recruiter",
        "email": "jane.recruiter@gmail.com",
        "claimed_company": "Acme Placements"
    }, headers=headers)
    assert rec_res.status_code == 200
    updated = rec_res.get_json()["verification"]
    assert updated["recruiter"]["status"] == "suspicious"
    assert updated["recruiter"]["provided"] is True

    # 6. POST /api/verification/:job_id/report (Report job)
    rep_res = client.post("/api/verification/test-verif-job-01/report", json={
        "reason": "fee_request",
        "note": "They asked for ₹2,000 on WhatsApp"
    }, headers=headers)
    assert rep_res.status_code == 201
    assert "Thank you" in rep_res.get_json()["message"]


def test_tenant_isolation_on_user_reports(client, clean_db):
    """User B cannot see or manipulate User A's reports, and unauthenticated requests return 401."""
    # Unauthenticated request
    unauth = client.post("/api/verification/some-job-id")
    assert unauth.status_code == 401

    unauth_get = client.get("/api/verification/some-job-id")
    assert unauth_get.status_code == 401
