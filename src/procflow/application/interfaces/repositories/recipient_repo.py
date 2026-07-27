"""Recipient repository interface."""

from __future__ import annotations

from typing import Protocol

from procflow.domain.entities import Recipient


class RecipientRepository(Protocol):
    def add(self, recipient: Recipient) -> Recipient:
        """Persist a new recipient. Returns it with ``id`` populated."""
        ...

    def get(self, recipient_id: int) -> Recipient:
        """Fetch by id or raise RecipientNotFoundError."""
        ...

    def list_all(self, *, query: str | None = None) -> list[Recipient]:
        """Return recipients, optionally filtered by substring in name/phone/address/purpose."""
        ...

    def update(self, recipient: Recipient) -> None:
        """Update mutable fields (name, purpose, phone, address, block, notes)."""
        ...

    def delete(self, recipient_id: int) -> None:
        """Remove the recipient."""
        ...
