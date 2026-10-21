"""Stage change repository interface."""

from __future__ import annotations

from typing import Protocol

from procflow.domain.entities import StageChange


class StageChangeRepository(Protocol):
    def add(self, change: StageChange) -> StageChange:
        """Persist a stage transition. Returns it with ``id`` populated."""
        ...

    def list_for_item(self, line_item_id: int) -> list[StageChange]:
        """Return transitions of one line item, oldest first."""
        ...

    def latest_for_items(self, line_item_ids: list[int]) -> dict[int, StageChange]:
        """Return the most recent transition per line item (missing keys = no history)."""
        ...
