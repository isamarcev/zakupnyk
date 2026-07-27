"""Offer repository interface."""

from __future__ import annotations

from typing import Protocol

from procflow.domain.entities import LineItem, Offer, Supplier


class OfferRepository(Protocol):
    def add(self, offer: Offer) -> Offer:
        """Persist a new offer. Returns it with ``id`` populated."""
        ...

    def get(self, offer_id: int) -> Offer:
        """Fetch by id or raise OfferNotFoundError."""
        ...

    def list_for_item(self, line_item_id: int) -> list[tuple[Offer, Supplier]]:
        """Return offers of one line item joined with their suppliers."""
        ...

    def list_for_supplier(self, supplier_id: int) -> list[tuple[Offer, LineItem]]:
        """Return offers of one supplier joined with their line items."""
        ...

    def delete(self, offer_id: int) -> None:
        """Remove the offer."""
        ...
