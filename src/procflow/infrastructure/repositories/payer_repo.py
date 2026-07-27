"""SQLAlchemy implementation of the payer repository."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from procflow.domain.entities import Payer
from procflow.domain.exceptions import PayerNotFoundError
from procflow.infrastructure.database import PayerRow
from procflow.infrastructure.repositories.mappers import payer_from_row


@dataclass(slots=True)
class SqlPayerRepository:
    session: Session

    def add(self, payer: Payer) -> Payer:
        row = PayerRow(
            name=payer.name,
            requisites=payer.requisites,
            iban=payer.iban,
            tax_id=payer.tax_id,
            bank=payer.bank,
            notes=payer.notes,
            created_at=payer.created_at,
        )
        self.session.add(row)
        self.session.flush()
        payer.id = row.id
        return payer

    def get(self, payer_id: int) -> Payer:
        row = self.session.get(PayerRow, payer_id)
        if row is None:
            raise PayerNotFoundError(f"Платника #{payer_id} не знайдено")
        return payer_from_row(row)

    def list_all(self, *, query: str | None = None) -> list[Payer]:
        stmt = select(PayerRow).order_by(PayerRow.name)
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    PayerRow.name.ilike(pattern),
                    PayerRow.requisites.ilike(pattern),
                    PayerRow.iban.ilike(pattern),
                    PayerRow.tax_id.ilike(pattern),
                )
            )
        return [payer_from_row(r) for r in self.session.scalars(stmt)]

    def update(self, payer: Payer) -> None:
        assert payer.id is not None
        row = self.session.get(PayerRow, payer.id)
        if row is None:
            raise PayerNotFoundError(f"Платника #{payer.id} не знайдено")
        row.name = payer.name
        row.requisites = payer.requisites
        row.iban = payer.iban
        row.tax_id = payer.tax_id
        row.bank = payer.bank
        row.notes = payer.notes
        self.session.flush()

    def delete(self, payer_id: int) -> None:
        row = self.session.get(PayerRow, payer_id)
        if row is None:
            raise PayerNotFoundError(f"Платника #{payer_id} не знайдено")
        self.session.delete(row)
        self.session.flush()
