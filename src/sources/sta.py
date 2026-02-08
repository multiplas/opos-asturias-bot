from __future__ import annotations

import logging
import re
from typing import Iterable
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from ..models import Item
from ..utils import fetch, make_hash_id, normalize_whitespace


logger = logging.getLogger(__name__)

EMPLOYMENT_HINTS = (
    "empleo",
    "convocatoria",
    "oferta",
    "bolsa",
    "tablon",
    "seleccion",
    "personal",
)

DATE_RE = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b")


def _extract_date(text: str) -> str | None:
    match = DATE_RE.search(text)
    return match.group(0) if match else None


def _discover_links(base_url: str, soup: BeautifulSoup) -> list[str]:
    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        text = normalize_whitespace(anchor.get_text(" ", strip=True)).lower()
        href = anchor["href"].strip()
        if any(hint in text for hint in EMPLOYMENT_HINTS) or any(
            hint in href.lower() for hint in EMPLOYMENT_HINTS
        ):
            absolute = urljoin(base_url, href)
            links.append(absolute)
    if not links:
        links = [base_url]
    return sorted(set(links))


def _parse_items(source_id: str, page_url: str, html: str) -> list[Item]:
    soup = BeautifulSoup(html, "html.parser")
    items: list[Item] = []
    for anchor in soup.find_all("a", href=True):
        if anchor.find_parent(["nav", "header", "footer"]):
            continue
        title = normalize_whitespace(anchor.get_text(" ", strip=True))
        if not title or len(title) < 6:
            continue
        href = anchor["href"].strip()
        if href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        if "PAGE_CODE=SEDE_" in href and "EMPLEO" not in href and "PTS2_EMPLEO" not in href:
            continue
        href = urljoin(page_url, href)
        text_context = anchor.parent.get_text(" ", strip=True)
        date = _extract_date(text_context)
        item_id = make_hash_id(source_id, title, href, date or "")
        items.append(
            Item(
                id=item_id,
                source_id=source_id,
                title=title,
                url=href,
                date=date,
                raw={"context": text_context},
            )
        )
    return items


def _discover_pagination(page_url: str, soup: BeautifulSoup) -> list[str]:
    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        text = normalize_whitespace(anchor.get_text(" ", strip=True)).lower()
        if text in {"siguiente", "sig", ">", ">>"} or "page" in anchor["href"]:
            links.append(urljoin(page_url, anchor["href"].strip()))
    return sorted(set(links))


def fetch_sta(source_id: str, url: str, max_pages: int = 3) -> Iterable[Item]:
    logger.info("STA: fetching base %s", url)
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    base_links = _discover_links(url, soup)
    seen_pages: set[str] = set()
    items: list[Item] = []

    for link in base_links:
        if link in seen_pages:
            continue
        if urlparse(link).netloc != urlparse(url).netloc:
            continue
        pending = [link]
        while pending and len(seen_pages) < max_pages:
            page = pending.pop(0)
            if page in seen_pages:
                continue
            seen_pages.add(page)
            try:
                page_html = fetch(page)
            except RuntimeError as exc:
                logger.warning("STA: failed to fetch %s: %s", page, exc)
                continue
            page_soup = BeautifulSoup(page_html, "html.parser")
            items.extend(_parse_items(source_id, page, page_html))
            for next_link in _discover_pagination(page, page_soup):
                if next_link not in seen_pages and next_link not in pending:
                    pending.append(next_link)
    return items
