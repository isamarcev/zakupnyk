"""Queries for supplier list and details."""

from __future__ import annotations

from dataclasses import dataclass

from procflow.application.dto import SupplierDetails
from procflow.application.interfaces.repositories import (
    DocumentRepository,
    OfferRepository,
    SupplierRepository,
)
from procflow.domain.entities import Supplier


@dataclass(slots=True)
class ListSuppliers:
    suppliers: SupplierRepository

    def __call__(self, *, name_query: str | None = None) -> list[Supplier]:
        return self.suppliers.list_all(name_query=name_query)


@dataclass(slots=True)
class GetSupplierDetails:
    suppliers: SupplierRepository
    offers: OfferRepository
    documents: DocumentRepository

    def __call__(self, supplier_id: int) -> SupplierDetails:
        supplier = self.suppliers.get(supplier_id)
        return SupplierDetails(
            supplier=supplier,
            offers=self.offers.list_for_supplier(supplier_id),
            documents=self.documents.search(supplier_id=supplier_id),
        )
