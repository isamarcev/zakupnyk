"""SQLAlchemy implementation of the supplier repository."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from procflow.domain.entities import Supplier
from procflow.domain.exceptions import SupplierNotFoundError
from procflow.infrastructure.database import SupplierRow
from procflow.infrastructure.repositories.mappers import supplier_from_row


@dataclass(slots=True)
class SqlSupplierRepository:
    session: Session

    def add(self, supplier: Supplier) -> Supplier:
        row = SupplierRow(
            name=supplier.name,
            source=supplier.source.value,
            contacts=supplier.contacts,
            notes=supplier.notes,
            created_at=supplier.created_at,
        )
        self.session.add(row)
        self.session.flush()
        supplier.id = row.id
        return supplier

    def get(self, supplier_id: int) -> Supplier:
        row = self.session.get(SupplierRow, supplier_id)
        if row is None:
            raise SupplierNotFoundError(f"Постачальника #{supplier_id} не знайдено")
        return supplier_from_row(row)

    def get_by_name(self, name: str) -> Supplier | None:
        row = self.session.scalars(select(SupplierRow).where(SupplierRow.name == name)).first()
        return supplier_from_row(row) if row is not None else None

    def list_all(self, *, name_query: str | None = None) -> list[Supplier]:
        stmt = select(SupplierRow).order_by(SupplierRow.name)
        if name_query:
            stmt = stmt.where(SupplierRow.name.ilike(f"%{name_query}%"))
        return [supplier_from_row(r) for r in self.session.scalars(stmt)]

    def update(self, supplier: Supplier) -> None:
        assert supplier.id is not None
        row = self.session.get(SupplierRow, supplier.id)
        if row is None:
            raise SupplierNotFoundError(f"Постачальника #{supplier.id} не знайдено")
        row.name = supplier.name
        row.source = supplier.source.value
        row.contacts = supplier.contacts
        row.notes = supplier.notes
        self.session.flush()

    def delete(self, supplier_id: int) -> None:
        row = self.session.get(SupplierRow, supplier_id)
        if row is None:
            raise SupplierNotFoundError(f"Постачальника #{supplier_id} не знайдено")
        self.session.delete(row)
        self.session.flush()
