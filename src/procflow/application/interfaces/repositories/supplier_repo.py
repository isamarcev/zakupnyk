"""Supplier repository interface."""

from __future__ import annotations

from typing import Protocol

from procflow.domain.entities import Supplier


class SupplierRepository(Protocol):
    def add(self, supplier: Supplier) -> Supplier:
        """Persist a new supplier. Returns it with ``id`` populated."""
        ...

    def get(self, supplier_id: int) -> Supplier:
        """Fetch by id or raise SupplierNotFoundError."""
        ...

    def get_by_name(self, name: str) -> Supplier | None:
        """Fetch by exact name (used by import dedup) or None."""
        ...

    def list_all(self, *, name_query: str | None = None) -> list[Supplier]:
        """Return suppliers, optionally filtered by case-insensitive substring."""
        ...

    def update(self, supplier: Supplier) -> None:
        """Update mutable fields (name, source, contacts, notes)."""
        ...

    def delete(self, supplier_id: int) -> None:
        """Remove the supplier; offers referencing it are removed too."""
        ...
