"""Procurement and line-item repository interfaces.

Implementations live in ``infrastructure/repositories``. Application code depends
only on these Protocols — that is the Dependency Inversion boundary.
"""

from __future__ import annotations

from typing import Protocol

from procflow.domain.entities import LineItem, Procurement


class ProcurementRepository(Protocol):
    def add(self, procurement: Procurement) -> Procurement:
        """Persist a new procurement. Returns it with ``id`` populated."""
        ...

    def get(self, procurement_id: int) -> Procurement:
        """Fetch by id or raise ProcurementNotFoundError."""
        ...

    def list_all(self) -> list[Procurement]:
        """Return all procurements, newest first."""
        ...

    def update(self, procurement: Procurement) -> None:
        """Update mutable fields (name, description, status, updated_at)."""
        ...

    def delete(self, procurement_id: int) -> None:
        """Remove the procurement and cascade (items, offers, documents)."""
        ...


class LineItemRepository(Protocol):
    def add(self, item: LineItem) -> LineItem:
        """Persist a new line item. Returns it with ``id`` populated."""
        ...

    def get(self, item_id: int) -> LineItem:
        """Fetch by id or raise LineItemNotFoundError."""
        ...

    def list_for_procurement(self, procurement_id: int) -> list[LineItem]:
        """Return items of one procurement in insertion order."""
        ...

    def update(self, item: LineItem) -> None:
        """Update mutable fields (name, spec, quantities, price)."""
        ...

    def delete(self, item_id: int) -> None:
        """Remove the item and its offers."""
        ...
