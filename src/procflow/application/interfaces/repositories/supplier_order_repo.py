"""Supplier order repository interface."""

from __future__ import annotations

from typing import Protocol

from procflow.domain.entities import SupplierOrder


class SupplierOrderRepository(Protocol):
    def add(self, order: SupplierOrder) -> SupplierOrder:
        """Persist a new order. Returns it with ``id`` populated."""
        ...

    def get(self, order_id: int) -> SupplierOrder:
        """Fetch by id or raise SupplierOrderNotFoundError."""
        ...

    def list_for_procurement(self, procurement_id: int) -> list[SupplierOrder]:
        """Return orders of one procurement in creation order."""
        ...

    def update(self, order: SupplierOrder) -> None:
        """Update mutable fields (title, supplier, note)."""
        ...

    def delete(self, order_id: int) -> None:
        """Remove the order; its items and documents stay, just unlinked."""
        ...
