"""Payer repository interface."""

from __future__ import annotations

from typing import Protocol

from procflow.domain.entities import Payer


class PayerRepository(Protocol):
    def add(self, payer: Payer) -> Payer:
        """Persist a new payer. Returns it with ``id`` populated."""
        ...

    def get(self, payer_id: int) -> Payer:
        """Fetch by id or raise PayerNotFoundError."""
        ...

    def list_all(self, *, query: str | None = None) -> list[Payer]:
        """Return payers, optionally filtered by substring in name/IBAN/tax id."""
        ...

    def update(self, payer: Payer) -> None:
        """Update mutable fields (name, iban, tax_id, bank, notes)."""
        ...

    def delete(self, payer_id: int) -> None:
        """Remove the payer; documents keep working (payer link becomes NULL)."""
        ...
