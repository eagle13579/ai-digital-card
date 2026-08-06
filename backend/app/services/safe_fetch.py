"""SSRF-safe HTTP fetching middleware — GET + POST support."""
import sys
sys.path.insert(0, 'D:/baize_libs')
from graph_tools.security_fetch import (
    validate_url as _validate_url,
    safe_fetch as _safe_fetch,
    safe_fetch_text as _safe_fetch_text,
)
import httpx

__all__ = [
    'validate_url', 'safe_fetch', 'safe_fetch_text',
    'safe_fetch_raw', 'SSRFError',
]

class SSRFError(ValueError):
    """Raised when URL fails SSRF validation."""
    pass

def validate_url(url: str) -> None:
    """Validate URL for SSRF safety. Raises SSRFError on bad URLs."""
    try:
        _validate_url(url)
    except ValueError as e:
        raise SSRFError(str(e))

def safe_fetch(
    url: str,
    max_bytes: int = 5 * 1024 * 1024,
    timeout: int = 30,
    method: str = "GET",
    content: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> bytes:
    """SSRF-safe HTTP fetch (GET or POST). Returns response body bytes.

    Raises SSRFError on invalid URLs, httpx.HTTPError on HTTP errors.
    """
    validate_url(url)
    limits = httpx.Limits(max_response_body=max_bytes)
    with httpx.Client(
        limits=limits,
        timeout=httpx.Timeout(timeout),
        follow_redirects=True,
    ) as client:
        response = client.request(method, url, content=content, headers=headers)
        response.raise_for_status()
        return response.content

def safe_fetch_raw(
    url: str,
    max_bytes: int = 1024 * 1024,
    timeout: int = 30,
    method: str = "GET",
    content: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, bytes]:
    """SSRF-safe fetch returning (status_code, body) without raising on HTTP errors.

    Useful for webhook dispatch where 4xx/5xx responses need to be inspected
    rather than raised.  Only network-level errors (connection refused, DNS
    failure, timeout, …) will raise exceptions.
    """
    validate_url(url)
    limits = httpx.Limits(max_response_body=max_bytes)
    with httpx.Client(
        limits=limits,
        timeout=httpx.Timeout(timeout),
        follow_redirects=True,
    ) as client:
        response = client.request(method, url, content=content, headers=headers)
        return response.status_code, response.content

def safe_fetch_text(url: str, max_bytes: int = 1024 * 1024, timeout: int = 30) -> str:
    """SSRF-safe text fetch (GET only)."""
    data = safe_fetch(url, max_bytes=max_bytes, timeout=timeout)
    return data.decode("utf-8", errors="replace")
