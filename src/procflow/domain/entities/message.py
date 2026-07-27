"""Message entity: a free-text note in a line item's timeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class ItemMessage:
    """One entry in the message thread of an order position."""

    id: int | None
    line_item_id: int
    text: str
    created_at: datetime = field(default_factory=datetime.now)
