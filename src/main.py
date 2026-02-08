from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Iterable

import yaml

from .models import Item
from .notifier import send_telegram
from .sources import fetch_age_buscador, fetch_principado_tablon, fetch_sta
from .state import is_new_item, load_state, mark_seen, save_state
from .utils import make_hash_id, normalize_whitespace


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _load_sources(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def _normalize_keywords(values: Iterable[str]) -> list[str]:
    return [normalize_whitespace(v).lower() for v in values if v and v.strip()]


def _matches_keywords(item: Item, include: list[str], exclude: list[str], match_any: bool) -> bool:
    if match_any:
        return True
    text = " ".join(
        [
            item.title or "",
            item.url or "",
            item.date or "",
            item.deadline or "",
            item.organization or "",
            str(item.raw) if item.raw else "",
        ]
    ).lower()
    if exclude and any(keyword in text for keyword in exclude):
        return False
    if include:
        return any(keyword in text for keyword in include)
    return True


def _fetch_items(source: dict[str, Any]) -> Iterable[Item]:
    source_id = source["id"]
    url = source["url"]
    source_type = source.get("type", "sta")
    if source_type == "sta":
        return fetch_sta(source_id, url)
    if source_type == "principado":
        return fetch_principado_tablon(source_id, url)
    if source_type == "age":
        return fetch_age_buscador(source_id, url)
    raise ValueError(f"Unknown source type: {source_type}")


def _summary_item(extra_count: int) -> Item:
    title = f"Resumen: {extra_count} avisos adicionales no enviados para evitar spam."
    return Item(
        id=make_hash_id("summary", title),
        source_id="RESUMEN",
        title=title,
        url="https://github.com/",
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sources_path = repo_root / "data" / "sources.yaml"
    state_path = repo_root / "data" / "state.json"

    config = _load_sources(sources_path)
    sources = config.get("sources", [])
    default_include = _normalize_keywords(config.get("include_keywords", []))
    default_exclude = _normalize_keywords(config.get("exclude_keywords", []))
    state = load_state(state_path)

    bot_token = os.getenv("BOT_TOKEN", "")
    chat_id = os.getenv("CHAT_ID", "")

    new_items: list[Item] = []

    for source in sources:
        source_id = source["id"]
        include = _normalize_keywords(source.get("include_keywords", [])) or default_include
        exclude = _normalize_keywords(source.get("exclude_keywords", [])) or default_exclude
        match_any = bool(source.get("match_any", False))

        try:
            items = list(_fetch_items(source))
        except Exception as exc:
            logger.warning("Source %s failed: %s", source_id, exc)
            continue

        logger.info("Source %s returned %d items", source_id, len(items))
        for item in items:
            if not _matches_keywords(item, include, exclude, match_any):
                continue
            if is_new_item(state, item):
                new_items.append(item)
            mark_seen(state, item)

    if new_items:
        logger.info("New items detected: %d", len(new_items))
        new_items.sort(key=lambda x: x.date or "", reverse=True)
        if len(new_items) > 15:
            extra = len(new_items) - 15
            notify_items = new_items[:15] + [_summary_item(extra)]
        else:
            notify_items = new_items
        send_telegram(notify_items, bot_token, chat_id)
    else:
        logger.info("No new items detected.")

    save_state(state_path, state)


if __name__ == "__main__":
    main()
