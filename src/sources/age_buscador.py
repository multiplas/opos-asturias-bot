from __future__ import annotations

import logging
import re
from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..models import Item
from ..utils import fetch, make_hash_id, normalize_whitespace


logger = logging.getLogger(__name__)

DATE_RE = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b")


def _extract_date(text: str) -> str | None:
    match = DATE_RE.search(text)
    return match.group(0) if match else None


def fetch_age_buscador(source_id: str, url: str) -> Iterable[Item]:
    logger.info("AGE buscador: fetching %s", url)
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    items: list[Item] = []

    results = soup.find("main") or soup
    for anchor in results.find_all("a", href=True):
        title = normalize_whitespace(anchor.get_text(" ", strip=True))
        if not title or len(title) < 6:
            continue
        href = urljoin(url, anchor["href"].strip())
        context = anchor.parent.get_text(" ", strip=True)
        date = _extract_date(context)
        item_id = make_hash_id(source_id, title, href, date or "")
        items.append(
            Item(
                id=item_id,
                source_id=source_id,
                title=title,
                url=href,
                date=date,
                raw={"context": context},
            )
        )
    if not items:
        logger.warning(
            "AGE buscador: no items parsed from HTML; the site may require parameters."
        )
    return items
