"""SQLAlchemy implementation of the offer repository."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from procflow.domain.entities import LineItem, Offer, Supplier
from procflow.domain.exceptions import OfferNotFoundError
from procflow.infrastructure.database import LineItemRow, OfferRow, SupplierRow
from procflow.infrastructure.repositories.mappers import (
    line_item_from_row,
    offer_from_row,
    supplier_from_row,
)


@dataclass(slots=True)
class SqlOfferRepository:
    session: Session

    def add(self, offer: Offer) -> Offer:
        row = OfferRow(
            line_item_id=offer.line_item_id,
            supplier_id=offer.supplier_id,
            url=offer.url,
            price=offer.price,
            note=offer.note,
            created_at=offer.created_at,
        )
        self.session.add(row)
        self.session.flush()
        offer.id = row.id
        return offer

    def get(self, offer_id: int) -> Offer:
        row = self.session.get(OfferRow, offer_id)
        if row is None:
            raise OfferNotFoundError(f"Пропозицію #{offer_id} не знайдено")
        return offer_from_row(row)

    def list_for_item(self, line_item_id: int) -> list[tuple[Offer, Supplier]]:
        rows = self.session.execute(
            select(OfferRow, SupplierRow)
            .join(SupplierRow, OfferRow.supplier_id == SupplierRow.id)
            .where(OfferRow.line_item_id == line_item_id)
            .order_by(OfferRow.price.is_(None), OfferRow.price)
        )
        return [(offer_from_row(o), supplier_from_row(s)) for o, s in rows]

    def list_for_supplier(self, supplier_id: int) -> list[tuple[Offer, LineItem]]:
        rows = self.session.execute(
            select(OfferRow, LineItemRow)
            .join(LineItemRow, OfferRow.line_item_id == LineItemRow.id)
            .where(OfferRow.supplier_id == supplier_id)
            .order_by(OfferRow.id.desc())
        )
        return [(offer_from_row(o), line_item_from_row(i)) for o, i in rows]

    def delete(self, offer_id: int) -> None:
        row = self.session.get(OfferRow, offer_id)
        if row is None:
            raise OfferNotFoundError(f"Пропозицію #{offer_id} не знайдено")
        self.session.delete(row)
        self.session.flush()
