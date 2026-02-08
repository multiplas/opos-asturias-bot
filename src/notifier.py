from __future__ import annotations

import logging
from typing import Iterable

import requests

from .models import Item


logger = logging.getLogger(__name__)


def _format_item(item: Item) -> str:
    parts = [f"📌 [{item.source_id}] {item.title}"]
    if item.date:
        parts.append(f"📅 {item.date}")
    if item.deadline:
        parts.append(f"🕒 {item.deadline}")
    if item.organization:
        parts.append(f"🏛️ {item.organization}")
    parts.append(f"🔗 {item.url}")
    return "\n".join(parts)


def send_telegram(items: Iterable[Item], bot_token: str, chat_id: str) -> None:
    if not bot_token or not chat_id:
        logger.info("Telegram credentials missing; running in dry-run mode.")
        for item in items:
            logger.info("DRY-RUN telegram message:\n%s", _format_item(item))
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    session = requests.Session()
    for item in items:
        payload = {
            "chat_id": chat_id,
            "text": _format_item(item),
            "disable_web_page_preview": True,
        }
        response = session.post(url, data=payload, timeout=20)
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Failed to send Telegram message for %s: %s", item.url, exc)
