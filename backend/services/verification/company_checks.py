"""
Company Verification Checks for CareerPilot AI (Module 6).
Evaluates domain consistency, ATS allowlists, typosquatting, HTTPS/TLD sanity,
careers page presence, MCA registration records, and RDAP domain age.
"""

import os
import json
import re
import socket
import difflib
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple, Optional
from abc import ABC, abstractmethod

from backend.config import Config
from backend.services.verification.network_safety import safe_request, is_safe_url


def _load_rules() -> Dict[str, Any]:
    rules_path = Config.VERIFICATION_RULES_PATH
    if os.path.exists(rules_path):
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "ats_allowlist": [],
        "url_shorteners": [],
        "suspicious_tlds": [],
        "multi_part_tlds": [".co.in", ".co.uk", ".com.au", ".org.in", ".edu.in", ".gov.in"]
    }


def extract_base_domain(url_or_domain: str) -> Optional[str]:
    """
    Extracts the registered base domain (e.g. 'infosys.com' from 'https://careers.infosys.com/job/123').
    Accounts for common multi-part TLDs (e.g., '.co.in', '.co.uk').
    """
    if not url_or_domain:
        return None

    cleaned = url_or_domain.strip().lower()
    if "://" in cleaned:
        try:
            cleaned = urlparse(cleaned).netloc
        except Exception:
            pass

    # Strip port if present
    if ":" in cleaned:
        cleaned = cleaned.split(":")[0]

    # Strip trailing dots or slashes
    cleaned = cleaned.strip("./")
    if not cleaned:
        return None

    rules = _load_rules()
    multi_part_tlds = rules.get("multi_part_tlds", [".co.in", ".co.uk", ".com.au", ".org.in", ".edu.in", ".gov.in"])

    # Check multi-part TLDs first
    for mp_tld in multi_part_tlds:
        if cleaned.endswith(mp_tld):
            remainder = cleaned[:-len(mp_tld)]
            parts = remainder.split(".")
            if parts and parts[-1]:
                return f"{parts[-1]}{mp_tld}"

    # Standard single-part TLD
    parts = cleaned.split(".")
    if len(parts) >= 2:
        return f"{parts[-2]}.{parts[-1]}"

    return cleaned


def normalize_company_name(name: str) -> str:
    """Normalizes company name for string and slug matching."""
    s = (name or "").lower()
    # Strip common suffixes
    s = re.sub(r"\b(technologies|technology|tech|solutions|solution|labs|lab|private|pvt|ltd|limited|inc|corp|corporation|group|llc|co)\b", "", s)
    s = re.sub(r"[^a-z0-9]", "", s)
    return s.strip()


# ---------------------------------------------------------------------------
# 1. Registration Lookup Interface & MCA Adapter
# ---------------------------------------------------------------------------

class RegistrationLookup(ABC):
    @abstractmethod
    def lookup_company(self, company_name: str) -> Dict[str, Any]:
        """Looks up company registration status."""
        pass


class MCALookupAdapter(RegistrationLookup):
    """
    Ministry of Corporate Affairs (India) Registration Adapter.
    MCA uses CAPTCHAs and has no free open public API. We provide:
    1. A deep link allowing candidates to verify manually on the official portal.
    2. An optional licensed data API adapter if MCA_API_KEY is configured.
    """

    def lookup_company(self, company_name: str) -> Dict[str, Any]:
        deep_link = "https://www.mca.gov.in/mcafoportal/viewCompanyMasterData.do"

        # If a commercial / licensed API key is configured in env:
        if Config.MCA_API_KEY:
            # Pluggable licensed lookup adapter logic could be placed here
            pass

        return {
            "result": "unavailable",
            "detail": "MCA portal requires CAPTCHA verification for automated access. Manual verification deep link provided.",
            "source_url": deep_link,
            "action_label": "Check manually on MCA",
            "manual_check_available": True
        }


# ---------------------------------------------------------------------------
# 2. Company Verification Checks
# ---------------------------------------------------------------------------

def run_company_checks(
    company_name: str,
    application_url: str,
    company_domain: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[str], List[Dict[str, Any]]]:
    """
    Executes modular checks for company legitimacy:
    1. Domain extraction & ATS allowlist vs direct domain consistency.
    2. HTTPS and domain sanity (raw IP, suspicious TLD, shorteners, subdomains).
    3. Typosquatting / look-alike domain detection.
    4. Careers page existence.
    5. MCA Registration deep link.
    6. Domain age via RDAP.

    Returns: (evidence_list, missing_list, warnings_list)
    """
    evidence: List[Dict[str, Any]] = []
    missing: List[str] = []
    warnings: List[Dict[str, Any]] = []
    now_iso = datetime.now(timezone.utc)

    rules = _load_rules()
    ats_allowlist = set(rules.get("ats_allowlist", []))
    url_shorteners = set(rules.get("url_shorteners", []))
    suspicious_tlds = set(rules.get("suspicious_tlds", []))

    parsed_app_url = urlparse(application_url) if application_url else None
    app_host = (parsed_app_url.netloc if parsed_app_url else "").lower().split(":")[0]
    app_base_domain = extract_base_domain(app_host)

    # 1. HTTPS Check
    if parsed_app_url and parsed_app_url.scheme == "https":
        evidence.append({
            "check": "https_enforcement",
            "result": "pass",
            "detail": "Application URL uses secure HTTPS encryption.",
            "source_url": application_url,
            "checked_at": now_iso
        })
    elif parsed_app_url and parsed_app_url.scheme == "http":
        warnings.append({
            "code": "INSECURE_HTTP_APPLICATION_URL",
            "severity": "medium",
            "message": "Application URL uses insecure plain HTTP instead of encrypted HTTPS."
        })
    else:
        warnings.append({
            "code": "INVALID_APPLICATION_URL_SCHEME",
            "severity": "medium",
            "message": "Application URL does not use a recognized web protocol."
        })

    # 2. Raw IP / URL Shortener / Suspicious TLD / Excessive Subdomain Checks
    if app_host:
        # Check raw IP
        is_ip = False
        try:
            socket.inet_aton(app_host)
            is_ip = True
        except socket.error:
            pass

        if is_ip:
            warnings.append({
                "code": "RAW_IP_APPLICATION_URL",
                "severity": "high",
                "message": f"Application URL directs to a raw IP address ({app_host}) rather than a verified domain name."
            })

        # Check URL shortener
        if any(shortener in app_host for shortener in url_shorteners):
            warnings.append({
                "code": "URL_SHORTENER_DETECTED",
                "severity": "high",
                "message": f"Application URL uses a link shortener ({app_host}) that masks the real destination."
            })

        # Check suspicious TLD
        tld = app_host.split(".")[-1] if "." in app_host else ""
        if tld in suspicious_tlds:
            warnings.append({
                "code": "SUSPICIOUS_TOP_LEVEL_DOMAIN",
                "severity": "medium",
                "message": f"Application domain uses high-risk top-level domain '.{tld}' frequently linked with spam/disposable domains."
            })

        # Check excessive subdomains (>3 dots in hostname)
        if app_host.count(".") > 3:
            warnings.append({
                "code": "EXCESSIVE_SUBDOMAINS",
                "severity": "low",
                "message": f"Domain {app_host} has unusual subdomain nesting."
            })

    # 3. Domain Consistency & ATS Allowlist Check
    is_ats = False
    if app_base_domain and app_base_domain in ats_allowlist:
        is_ats = True
        evidence.append({
            "check": "ats_allowlist_match",
            "result": "pass",
            "detail": f"Application URL is hosted on recognized enterprise ATS/job board platform: '{app_base_domain}'.",
            "source_url": application_url,
            "checked_at": now_iso
        })
    elif app_base_domain:
        # Compare base domain with normalized company name
        norm_company = normalize_company_name(company_name)
        norm_domain_name = app_base_domain.split(".")[0].lower()

        # Check exact or partial inclusion
        if norm_company and (norm_company in norm_domain_name or norm_domain_name in norm_company):
            evidence.append({
                "check": "company_domain_match",
                "result": "pass",
                "detail": f"Application domain '{app_base_domain}' aligns with company identity '{company_name}'.",
                "source_url": application_url,
                "checked_at": now_iso
            })
        else:
            # Check typosquatting / edit-distance against normalized company name (check whole & hyphen-split tokens)
            tokens = [p for p in re.split(r"[-_]", norm_domain_name) if p] or [norm_domain_name]
            best_ratio = max(difflib.SequenceMatcher(None, norm_company, tok).ratio() for tok in tokens)
            if 0.65 <= best_ratio < 0.95:
                warnings.append({
                    "code": "LOOKALIKE_DOMAIN_DETECTED",
                    "severity": "medium",
                    "message": f"Domain '{app_base_domain}' closely resembles '{company_name}' (similarity {int(best_ratio*100)}%), which may indicate typosquatting."
                })
            else:
                missing.append(f"Application domain '{app_base_domain}' could not be automatically confirmed as belonging to '{company_name}'.")

    # 4. Official Careers Page Verification
    careers_domain = company_domain or (app_base_domain if not is_ats else None)
    if careers_domain and not any(shortener in careers_domain for shortener in url_shorteners):
        careers_url = f"https://{careers_domain}/careers"
        # SSRF-safe request
        resp, err = safe_request(careers_url, timeout=3)
        if resp and resp.status_code == 200:
            evidence.append({
                "check": "official_careers_page",
                "result": "pass",
                "detail": f"Official careers page responded successfully at {careers_url}.",
                "source_url": careers_url,
                "checked_at": now_iso
            })
        elif resp and resp.status_code in (403, 401):
            evidence.append({
                "check": "official_careers_page",
                "result": "unavailable",
                "detail": f"Careers portal responded with status {resp.status_code} (anti-bot or login required).",
                "source_url": careers_url,
                "checked_at": now_iso
            })
        else:
            missing.append(f"Official careers page could not be confirmed ({err or 'unreachable'}).")
    else:
        missing.append("No official independent corporate careers URL available for direct probing.")

    # 5. MCA India Registration Lookup Deep Link
    mca_adapter = MCALookupAdapter()
    mca_res = mca_adapter.lookup_company(company_name)
    evidence.append({
        "check": "mca_registration_check",
        "result": mca_res["result"],
        "detail": mca_res["detail"],
        "source_url": mca_res["source_url"],
        "checked_at": now_iso
    })

    # 6. RDAP Domain Age Check
    target_rdap_domain = app_base_domain if not is_ats else None
    if target_rdap_domain and not any(s in target_rdap_domain for s in url_shorteners):
        rdap_evidence, rdap_warning = check_domain_age_rdap(target_rdap_domain, now_iso)
        if rdap_evidence:
            evidence.append(rdap_evidence)
        if rdap_warning:
            warnings.append(rdap_warning)

    return evidence, missing, warnings


def check_domain_age_rdap(domain: str, now_iso: datetime) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Queries ICANN RDAP for domain registration date.
    Adds medium warning if domain age < DOMAIN_MIN_AGE_DAYS.
    """
    rdap_url = f"https://rdap.org/domain/{domain}"
    resp, err = safe_request(rdap_url, timeout=3)
    if not resp or resp.status_code != 200:
        return None, None

    try:
        data = resp.json()
        events = data.get("events", [])
        reg_date = None
        for evt in events:
            if evt.get("eventAction") in ("registration", "created"):
                reg_date_str = evt.get("eventDate")
                if reg_date_str:
                    try:
                        # Parse ISO date
                        clean_str = reg_date_str.replace("Z", "+00:00")
                        reg_date = datetime.fromisoformat(clean_str)
                    except Exception:
                        pass
                break

        if reg_date:
            age_days = (datetime.now(timezone.utc) - reg_date).days
            min_age = Config.DOMAIN_MIN_AGE_DAYS
            ev = {
                "check": "domain_age_rdap",
                "result": "pass",
                "detail": f"Domain '{domain}' was registered on {reg_date.strftime('%Y-%m-%d')} ({age_days} days old).",
                "source_url": rdap_url,
                "checked_at": now_iso
            }
            warn = None
            if age_days < min_age:
                warn = {
                    "code": "NEWLY_REGISTERED_DOMAIN",
                    "severity": "medium",
                    "message": f"Domain '{domain}' was registered recently ({age_days} days ago, below the {min_age}-day threshold)."
                }
            return ev, warn
    except Exception:
        pass

    return None, None
