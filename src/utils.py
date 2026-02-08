from __future__ import annotations

import hashlib
import time
from typing import Optional

import requests

USER_AGENT = "opos-asturias-bot/1.0 (+https://github.com/)"


_last_request_ts: Optional[float] = None


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def make_hash_id(*parts: str) -> str:
    normalized = "|".join(part.strip().lower() for part in parts if part)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def rate_limit_sleep(min_interval: float = 1.0) -> None:
    global _last_request_ts
    now = time.time()
    if _last_request_ts is not None:
        elapsed = now - _last_request_ts
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
    _last_request_ts = time.time()


def fetch(url: str, timeout: int = 20, retries: int = 3) -> str:
    headers = {"User-Agent": USER_AGENT}
    last_error: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            rate_limit_sleep()
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response.text
        except requests.RequestException as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1.0 * attempt)
            else:
                break
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")
