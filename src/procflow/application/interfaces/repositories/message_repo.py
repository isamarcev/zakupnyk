"""Message repository interface."""

from __future__ import annotations

from typing import Protocol

from procflow.domain.entities import ItemMessage


class MessageRepository(Protocol):
    def add(self, message: ItemMessage) -> ItemMessage:
        """Persist a new message. Returns it with ``id`` populated."""
        ...

    def list_for_item(self, line_item_id: int) -> list[ItemMessage]:
        """Return messages of one line item, newest first."""
        ...

    def latest_for_item(self, line_item_id: int) -> ItemMessage | None:
        """Return the most recent message of a line item, or None."""
        ...

    def delete(self, message_id: int) -> None:
        """Remove a message or raise MessageNotFoundError."""
        ...
