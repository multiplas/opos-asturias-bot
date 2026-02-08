from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import Item


State = dict[str, Any]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state(path: Path) -> State:
    if not path.exists():
        return {"sources": {}}
    content = path.read_text(encoding="utf-8")
    if not content.strip():
        return {"sources": {}}
    data = json.loads(content)
    if "sources" not in data:
        data["sources"] = {}
    return data


def save_state(path: Path, state: State) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_source_state(state: State, source_id: str) -> dict[str, Any]:
    sources = state.setdefault("sources", {})
    return sources.setdefault(source_id, {"seen": [], "updated_at": None})


def is_new_item(state: State, item: Item) -> bool:
    source_state = _get_source_state(state, item.source_id)
    return item.id not in set(source_state.get("seen", []))


def mark_seen(state: State, item: Item) -> None:
    source_state = _get_source_state(state, item.source_id)
    seen = set(source_state.get("seen", []))
    seen.add(item.id)
    source_state["seen"] = sorted(seen)
    source_state["updated_at"] = _now_iso()
