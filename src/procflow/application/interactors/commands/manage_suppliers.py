"""Commands for suppliers and offers."""

from __future__ import annotations

from dataclasses import dataclass

from procflow.application.dto import OfferInput, SupplierInput
from procflow.application.interfaces.repositories import (
    LineItemRepository,
    OfferRepository,
    SupplierRepository,
)
from procflow.domain.entities import Offer, Supplier, normalize_url
from procflow.domain.exceptions import InvalidInputError


@dataclass(slots=True)
class CreateSupplier:
    suppliers: SupplierRepository

    def __call__(self, data: SupplierInput) -> Supplier:
        name = data.name.strip()
        if not name:
            raise InvalidInputError("Назва постачальника не може бути порожньою")
        return self.suppliers.add(
            Supplier(
                id=None,
                name=name,
                source=data.source,
                contacts=data.contacts.strip(),
                notes=data.notes.strip(),
            )
        )


@dataclass(slots=True)
class UpdateSupplier:
    suppliers: SupplierRepository

    def __call__(self, supplier_id: int, data: SupplierInput) -> Supplier:
        supplier = self.suppliers.get(supplier_id)
        name = data.name.strip()
        if not name:
            raise InvalidInputError("Назва постачальника не може бути порожньою")
        supplier.name = name
        supplier.source = data.source
        supplier.contacts = data.contacts.strip()
        supplier.notes = data.notes.strip()
        self.suppliers.update(supplier)
        return supplier


@dataclass(slots=True)
class AddOffer:
    offers: OfferRepository
    items: LineItemRepository
    suppliers: SupplierRepository

    def __call__(self, data: OfferInput) -> Offer:
        self.items.get(data.line_item_id)  # raises if missing
        self.suppliers.get(data.supplier_id)  # raises if missing
        return self.offers.add(
            Offer(
                id=None,
                line_item_id=data.line_item_id,
                supplier_id=data.supplier_id,
                url=normalize_url(data.url),
                price=data.price,
                note=data.note.strip(),
            )
        )


@dataclass(slots=True)
class DeleteOffer:
    offers: OfferRepository

    def __call__(self, offer_id: int) -> None:
        self.offers.get(offer_id)  # raises if missing
        self.offers.delete(offer_id)
