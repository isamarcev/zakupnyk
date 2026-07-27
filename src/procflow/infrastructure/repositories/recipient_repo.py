"""SQLAlchemy implementation of the recipient repository."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from procflow.domain.entities import Recipient
from procflow.domain.exceptions import RecipientNotFoundError
from procflow.infrastructure.database import RecipientRow
from procflow.infrastructure.repositories.mappers import recipient_from_row


@dataclass(slots=True)
class SqlRecipientRepository:
    session: Session

    def add(self, recipient: Recipient) -> Recipient:
        row = RecipientRow(
            name=recipient.name,
            purpose=recipient.purpose,
            phone=recipient.phone,
            address=recipient.address,
            block=recipient.block,
            notes=recipient.notes,
            created_at=recipient.created_at,
        )
        self.session.add(row)
        self.session.flush()
        recipient.id = row.id
        return recipient

    def get(self, recipient_id: int) -> Recipient:
        row = self.session.get(RecipientRow, recipient_id)
        if row is None:
            raise RecipientNotFoundError(f"Отримувача #{recipient_id} не знайдено")
        return recipient_from_row(row)

    def list_all(self, *, query: str | None = None) -> list[Recipient]:
        stmt = select(RecipientRow).order_by(RecipientRow.name)
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    RecipientRow.name.ilike(pattern),
                    RecipientRow.purpose.ilike(pattern),
                    RecipientRow.phone.ilike(pattern),
                    RecipientRow.address.ilike(pattern),
                    RecipientRow.block.ilike(pattern),
                )
            )
        return [recipient_from_row(r) for r in self.session.scalars(stmt)]

    def update(self, recipient: Recipient) -> None:
        assert recipient.id is not None
        row = self.session.get(RecipientRow, recipient.id)
        if row is None:
            raise RecipientNotFoundError(f"Отримувача #{recipient.id} не знайдено")
        row.name = recipient.name
        row.purpose = recipient.purpose
        row.phone = recipient.phone
        row.address = recipient.address
        row.block = recipient.block
        row.notes = recipient.notes
        self.session.flush()

    def delete(self, recipient_id: int) -> None:
        row = self.session.get(RecipientRow, recipient_id)
        if row is None:
            raise RecipientNotFoundError(f"Отримувача #{recipient_id} не знайдено")
        self.session.delete(row)
        self.session.flush()
