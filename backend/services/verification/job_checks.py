"""
Job Posting Verification Checks for CareerPilot AI (Module 6).
Performs deterministic rule-based scanning for fee demands, credential theft,
WhatsApp/Telegram channels, salary guarantees, WFH no-interview patterns, and integrates
an optional AI second opinion with strict non-overriding constraints.
"""

import os
import json
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional

from backend.config import Config
from backend.services.verification.company_checks import extract_base_domain


def _load_rules() -> Dict[str, Any]:
    rules_path = Config.VERIFICATION_RULES_PATH
    if os.path.exists(rules_path):
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"job_suspicious_patterns": [], "url_shorteners": []}


def scan_job_description_for_scam_patterns(
    title: str,
    description: str
) -> List[Dict[str, Any]]:
    """
    Scans job title and description text against deterministic scam regexes.
    Returns a list of warning dicts with code, severity, message, and exact quote.
    """
    warnings: List[Dict[str, Any]] = []
    combined_text = f"{title or ''}\n{description or ''}"

    rules = _load_rules()
    patterns = rules.get("job_suspicious_patterns", [])

    for pat in patterns:
        code = pat.get("code")
        severity = pat.get("severity", "medium")
        regex_str = pat.get("regex")
        message = pat.get("message", "Suspicious pattern detected.")

        if not regex_str:
            continue

        try:
            match = re.search(regex_str, combined_text, flags=re.IGNORECASE)
            if match:
                matched_snippet = match.group(0).strip()
                warnings.append({
                    "code": code,
                    "severity": severity,
                    "message": message,
                    "exact_quote": matched_snippet[:150]
                })
        except re.error:
            pass

    return warnings


def run_job_posting_checks(
    job_doc: Dict[str, Any],
    ai_service=None
) -> Tuple[List[Dict[str, Any]], List[str], List[Dict[str, Any]]]:
    """
    Executes job posting level verification checks.
    Returns: (evidence_list, missing_list, warnings_list)
    """
    evidence: List[Dict[str, Any]] = []
    missing: List[str] = []
    warnings: List[Dict[str, Any]] = []
    now_iso = datetime.now(timezone.utc)

    title = job_doc.get("title", "")
    description = job_doc.get("description", "")
    application_url = job_doc.get("application_url", "")
    status = job_doc.get("status", "active")

    # 1. Deterministic scam pattern scan
    scam_warnings = scan_job_description_for_scam_patterns(title, description)
    warnings.extend(scam_warnings)

    if not scam_warnings:
        evidence.append({
            "check": "scam_indicator_scan",
            "result": "pass",
            "detail": "No upfront fee requests, credential harvesting, or unofficial chat channels detected in posting text.",
            "source_url": None,
            "checked_at": now_iso
        })

    # 2. Description completeness check
    word_count = len((description or "").split())
    if word_count < 25:
        warnings.append({
            "code": "VAGUE_JOB_DESCRIPTION",
            "severity": "medium",
            "message": f"Job description is unusually brief ({word_count} words). Legitimate engineering postings usually outline responsibilities and expectations in detail."
        })
    else:
        evidence.append({
            "check": "description_completeness",
            "result": "pass",
            "detail": f"Posting contains adequate detail ({word_count} words) regarding role scope and competencies.",
            "source_url": None,
            "checked_at": now_iso
        })

    # 3. Application URL check
    if not application_url or not application_url.strip():
        warnings.append({
            "code": "MISSING_APPLICATION_URL",
            "severity": "medium",
            "message": "Posting lacks an external application link."
        })
    else:
        rules = _load_rules()
        url_shorteners = set(rules.get("url_shorteners", []))
        app_domain = extract_base_domain(application_url) or ""
        if any(shortener in app_domain for shortener in url_shorteners):
            warnings.append({
                "code": "SHORTENED_APPLICATION_URL",
                "severity": "high",
                "message": f"Application link uses URL shortener ({app_domain}), which obscures destination and is typical of phishing links."
            })

    # 4. Expiration / Age check
    if status == "expired":
        warnings.append({
            "code": "EXPIRED_JOB_LISTING",
            "severity": "medium",
            "message": "This job listing is marked expired or has passed its stated application deadline."
        })

    # 5. Optional AI second opinion
    if ai_service is not None:
        try:
            ai_warnings = ai_service.check_job_suspicious_patterns(title, description)
            for ai_w in ai_warnings:
                # Enforce constraints: only low or medium severity, never high
                sev = ai_w.get("severity", "low")
                if sev == "high":
                    sev = "medium"
                warnings.append({
                    "code": "AI_DETECTED_CONCERN",
                    "severity": sev,
                    "message": f"AI-detected possible concern: {ai_w.get('message', '')}",
                    "exact_quote": ai_w.get("exact_quote")
                })
        except Exception:
            pass

    return evidence, missing, warnings
