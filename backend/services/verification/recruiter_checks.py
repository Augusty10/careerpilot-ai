"""
Recruiter Verification Checks for CareerPilot AI (Module 6).
Evaluates recruiter contact details, corporate domain alignment, free email impersonation,
look-alike domains, and provides safe manual LinkedIn search deep links.
"""

import os
import json
import difflib
from datetime import datetime, timezone
from urllib.parse import quote_plus
from typing import List, Dict, Any, Tuple, Optional

from backend.config import Config
from backend.services.verification.company_checks import extract_base_domain, normalize_company_name


def _load_rules() -> Dict[str, Any]:
    rules_path = Config.VERIFICATION_RULES_PATH
    if os.path.exists(rules_path):
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"free_email_domains": []}


def run_recruiter_checks(
    company_name: str,
    application_url: str,
    recruiter_name: Optional[str] = None,
    recruiter_email: Optional[str] = None,
    claimed_company: Optional[str] = None
) -> Tuple[bool, Dict[str, Any], List[Dict[str, Any]], List[str], List[Dict[str, Any]]]:
    """
    Executes recruiter checks if contact info is present.
    Returns: (provided, contact_dict, evidence_list, missing_list, warnings_list)
    """
    evidence: List[Dict[str, Any]] = []
    missing: List[str] = []
    warnings: List[Dict[str, Any]] = []
    now_iso = datetime.now(timezone.utc)

    # Clean and validate input
    rec_name = (recruiter_name or "").strip()
    rec_email = (recruiter_email or "").strip().lower()
    claimed = (claimed_company or company_name or "").strip()

    if not rec_email and not rec_name:
        return False, {
            "name": None,
            "email": None,
            "claimed_company": None
        }, evidence, ["No recruiter contact information was provided for this posting."], warnings

    contact_dict = {
        "name": rec_name or None,
        "email": rec_email or None,
        "claimed_company": claimed or None
    }

    rules = _load_rules()
    free_email_domains = set(rules.get("free_email_domains", []))

    # Recruiter email analysis
    if rec_email and "@" in rec_email:
        email_user, email_domain = rec_email.split("@", 1)
        email_base_domain = extract_base_domain(email_domain) or email_domain

        # 1. Free Email Impersonation Check (HIGH SEVERITY)
        if email_base_domain in free_email_domains or email_domain in free_email_domains:
            warnings.append({
                "code": "RECRUITER_FREE_EMAIL_PROVIDER",
                "severity": "high",
                "message": f"Recruiter contacted using a free personal email service (@{email_domain}) while claiming to represent '{claimed}'. Legitimate enterprise recruiters communicate via corporate domains."
            })
        else:
            # 2. Domain Alignment vs Company Domain
            company_base_domain = extract_base_domain(application_url) if application_url else None
            norm_company = normalize_company_name(claimed)
            norm_email_domain = email_base_domain.split(".")[0].lower()

            if company_base_domain and email_base_domain == company_base_domain:
                evidence.append({
                    "check": "recruiter_domain_match",
                    "result": "pass",
                    "detail": f"Recruiter email domain (@{email_base_domain}) matches verified corporate domain.",
                    "source_url": None,
                    "checked_at": now_iso
                })
            elif norm_company and norm_company in norm_email_domain:
                evidence.append({
                    "check": "recruiter_domain_match",
                    "result": "pass",
                    "detail": f"Recruiter email domain (@{email_base_domain}) reflects company identity '{claimed}'.",
                    "source_url": None,
                    "checked_at": now_iso
                })
            else:
                # Check look-alike / typosquatting domain
                ratio = difflib.SequenceMatcher(None, norm_company, norm_email_domain).ratio()
                if 0.65 <= ratio < 0.95:
                    warnings.append({
                        "code": "RECRUITER_LOOKALIKE_DOMAIN",
                        "severity": "high",
                        "message": f"Recruiter email domain (@{email_base_domain}) looks deceptively similar to '{claimed}' (similarity {int(ratio*100)}%), potential impersonation attempt."
                    })
                else:
                    warnings.append({
                        "code": "RECRUITER_DOMAIN_MISMATCH",
                        "severity": "medium",
                        "message": f"Recruiter email domain (@{email_base_domain}) does not match the company's verified domain or brand name."
                    })

    # 3. Professional Profile Deep Link (LinkedIn)
    search_query = f"{claimed} {rec_name}".strip()
    if search_query:
        encoded_query = quote_plus(search_query)
        linkedin_search_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded_query}"
        evidence.append({
            "check": "recruiter_professional_profile",
            "result": "unavailable",
            "detail": f"Direct scraping of LinkedIn is not permitted. You can verify recruiter credentials manually via LinkedIn search.",
            "source_url": linkedin_search_url,
            "checked_at": now_iso
        })
    else:
        missing.append("No recruiter name specified to perform professional profile checks.")

    # 4. Corporate Directory Check
    missing.append("Recruiter affiliation could not be automatically confirmed in an open public corporate directory.")

    return True, contact_dict, evidence, missing, warnings
