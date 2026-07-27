"""SQLAlchemy implementation of the message repository."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from procflow.domain.entities import ItemMessage
from procflow.domain.exceptions import MessageNotFoundError
from procflow.infrastructure.database import MessageRow
from procflow.infrastructure.repositories.mappers import message_from_row


@dataclass(slots=True)
class SqlMessageRepository:
    session: Session

    def add(self, message: ItemMessage) -> ItemMessage:
        row = MessageRow(
            line_item_id=message.line_item_id,
            text=message.text,
            created_at=message.created_at,
        )
        self.session.add(row)
        self.session.flush()
        message.id = row.id
        return message

    def list_for_item(self, line_item_id: int) -> list[ItemMessage]:
        rows = self.session.scalars(
            select(MessageRow)
            .where(MessageRow.line_item_id == line_item_id)
            .order_by(MessageRow.created_at.desc(), MessageRow.id.desc())
        )
        return [message_from_row(r) for r in rows]

    def latest_for_item(self, line_item_id: int) -> ItemMessage | None:
        row = self.session.scalars(
            select(MessageRow)
            .where(MessageRow.line_item_id == line_item_id)
            .order_by(MessageRow.created_at.desc(), MessageRow.id.desc())
            .limit(1)
        ).first()
        return message_from_row(row) if row is not None else None

    def delete(self, message_id: int) -> None:
        row = self.session.get(MessageRow, message_id)
        if row is None:
            raise MessageNotFoundError(f"Повідомлення #{message_id} не знайдено")
        self.session.delete(row)
        self.session.flush()
