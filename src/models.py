from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Item:
    id: str
    source_id: str
    title: str
    url: str
    date: Optional[str] = None
    deadline: Optional[str] = None
    organization: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict)
