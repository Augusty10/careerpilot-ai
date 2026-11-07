"""
Network Safety and SSRF Protection for CareerPilot AI Verification Engine.
Enforces strict host validation, private/internal IP blocking, timeout enforcement,
and redirect boundary verification.
"""

import socket
import ipaddress
from urllib.parse import urlparse
from typing import Tuple, Optional, Dict, Any
import requests

from backend.config import Config


USER_AGENT = "CareerPilotAI-Verifier/1.0 (+https://careerpilot.ai/bot)"
DEFAULT_MAX_REDIRECTS = 3
DEFAULT_MAX_BYTES = 1024 * 1024  # 1 MB


def is_safe_ip(ip_str: str) -> Tuple[bool, str]:
    """
    Validates whether an IP address is safe to query publicly.
    Rejects private, loopback, link-local (cloud metadata), reserved, and multicast IPs.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.is_loopback:
            return False, f"Loopback address blocked ({ip_str})"
        if ip.is_link_local:
            return False, f"Link-local cloud metadata address blocked ({ip_str})"
        if ip.is_private:
            return False, f"Private network address blocked ({ip_str})"
        if ip.is_reserved:
            return False, f"Reserved address blocked ({ip_str})"
        if ip.is_multicast:
            return False, f"Multicast address blocked ({ip_str})"
        if ip.is_unspecified:
            return False, f"Unspecified address blocked ({ip_str})"
        return True, "IP is safe"
    except ValueError:
        return False, f"Invalid IP address format: {ip_str}"


def is_safe_url(url: str) -> Tuple[bool, str, Optional[str]]:
    """
    Inspects a URL scheme, hostname, and resolved IP addresses to prevent SSRF attacks.
    Returns: (is_safe, reason, resolved_ip)
    """
    if not url or not isinstance(url, str):
        return False, "Empty or invalid URL", None

    try:
        parsed = urlparse(url.strip())
    except Exception as e:
        return False, f"Malformed URL: {e}", None

    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        return False, f"Unsupported URL scheme '{scheme}'. Only http and https are permitted.", None

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return False, "Missing hostname in URL", None

    # Check for direct localhost / literal keywords
    if hostname in ("localhost", "0.0.0.0", "127.0.0.1", "::1", "metadata.google.internal"):
        return False, f"Direct access to internal host '{hostname}' is blocked", None

    # Check if hostname itself is an IP literal
    try:
        is_safe, reason = is_safe_ip(hostname)
        if not is_safe:
            return False, reason, hostname
        return True, "Safe literal IP", hostname
    except Exception:
        pass

    # Resolve hostname via DNS and check all returned IPs
    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        if not addr_info:
            return False, f"DNS resolution yielded no addresses for {hostname}", None

        first_safe_ip = None
        for family, socktype, proto, canonname, sockaddr in addr_info:
            ip_candidate = sockaddr[0]
            safe, reason = is_safe_ip(ip_candidate)
            if not safe:
                return False, f"Resolved host {hostname} to unsafe IP {ip_candidate}: {reason}", None
            if not first_safe_ip:
                first_safe_ip = ip_candidate

        return True, "Host is safe", first_safe_ip
    except socket.gaierror as e:
        return False, f"DNS resolution failed for {hostname}: {e}", None
    except Exception as e:
        return False, f"Error resolving host {hostname}: {e}", None


def safe_request(
    url: str,
    method: str = "GET",
    timeout: Optional[int] = None,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
    max_bytes: int = DEFAULT_MAX_BYTES,
    headers: Optional[Dict[str, str]] = None
) -> Tuple[Optional[requests.Response], Optional[str]]:
    """
    Executes an HTTP request with strict SSRF protection, manual redirect validation,
    response size capping, and timeout enforcement.
    Returns: (response, error_message)
    """
    current_url = url
    session = requests.Session()
    req_timeout = timeout if timeout is not None else Config.VERIFICATION_NETWORK_TIMEOUT

    req_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8"
    }
    if headers:
        req_headers.update(headers)

    for redirect_count in range(max_redirects + 1):
        is_safe, reason, _ = is_safe_url(current_url)
        if not is_safe:
            return None, f"Blocked unsafe request to {current_url}: {reason}"

        try:
            resp = session.request(
                method=method,
                url=current_url,
                timeout=req_timeout,
                allow_redirects=False,
                headers=req_headers,
                stream=True
            )

            # Check redirect (301, 302, 303, 307, 308)
            if resp.status_code in (301, 302, 303, 307, 308):
                location = resp.headers.get("Location")
                if not location:
                    return resp, None
                # Resolve relative redirects
                from urllib.parse import urljoin
                current_url = urljoin(current_url, location)
                continue

            # Read up to max_bytes to prevent denial of service via oversized content
            content = resp.raw.read(max_bytes + 1, decode_content=True)
            resp._content = content[:max_bytes]
            return resp, None

        except requests.exceptions.Timeout:
            return None, f"Request to {current_url} timed out after {req_timeout}s"
        except requests.exceptions.SSLError as e:
            return None, f"SSL verification error for {current_url}: {e}"
        except requests.exceptions.RequestException as e:
            return None, f"Network error requesting {current_url}: {e}"
        except Exception as e:
            return None, f"Unexpected error requesting {current_url}: {e}"

    return None, f"Exceeded maximum allowed redirects ({max_redirects})"
