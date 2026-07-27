"""Import a parsed Excel needs-list as new procurements.

Each sheet becomes one procurement; rows become line items; per-source price
links become suppliers (deduplicated by name) and offers. Marketplace offers
(Prom, Rozetka) share one supplier per marketplace; distributor offers get a
named supplier derived from the link's domain — «дистриб'ютор» сам по собі
надто розмите поняття, у кожного товару він свій.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

from procflow.application.dto import ImportedSheet
from procflow.application.interfaces.repositories import (
    LineItemRepository,
    OfferRepository,
    ProcurementRepository,
    SupplierRepository,
)
from procflow.domain.entities import (
    LineItem,
    Offer,
    Procurement,
    ProcurementStatus,
    Supplier,
    SupplierSource,
    normalize_url,
)


@dataclass(slots=True)
class ImportNeeds:
    procurements: ProcurementRepository
    items: LineItemRepository
    suppliers: SupplierRepository
    offers: OfferRepository

    def __call__(self, sheets: list[ImportedSheet]) -> list[Procurement]:
        created: list[Procurement] = []
        for sheet in sheets:
            if not sheet.rows:
                continue
            created.append(self._import_sheet(sheet))
        return created

    def _import_sheet(self, sheet: ImportedSheet) -> Procurement:
        now = datetime.now()
        procurement = self.procurements.add(
            Procurement(
                id=None,
                name=sheet.title,
                description="Імпортовано з Excel",
                status=ProcurementStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )
        )
        assert procurement.id is not None
        for row in sheet.rows:
            item = self.items.add(
                LineItem(
                    id=None,
                    procurement_id=procurement.id,
                    name=row.name,
                    specification=row.specification,
                    qty_required=row.qty_required,
                    qty_ordered=row.qty_ordered,
                    qty_in_progress=row.qty_in_progress,
                    unit_price=row.unit_price,
                )
            )
            assert item.id is not None
            for offer in row.offers:
                supplier = self._supplier_for(offer.source, offer.url)
                assert supplier.id is not None
                self.offers.add(
                    Offer(
                        id=None,
                        line_item_id=item.id,
                        supplier_id=supplier.id,
                        url=normalize_url(offer.url),
                        price=offer.price,
                    )
                )
        return procurement

    def _supplier_for(self, source: SupplierSource, url: str) -> Supplier:
        """Find or create the supplier for an imported offer.

        Distributors are named after the link's domain (bnbfly.com.ua, …);
        marketplaces keep one shared supplier per marketplace.
        """
        name = source.label_uk
        if source is SupplierSource.DISTRIBUTOR:
            name = _domain_of(url) or name
        existing = self.suppliers.get_by_name(name)
        if existing is not None:
            return existing
        return self.suppliers.add(Supplier(id=None, name=name, source=source))


def _domain_of(url: str) -> str:
    """'https://www.bnbfly.com.ua/ua/p…' → 'bnbfly.com.ua'; '' when not a URL."""
    host = urlparse(url.strip()).netloc.lower()
    return host.removeprefix("www.")
