"""Commands for the line-item message thread."""

from __future__ import annotations

from dataclasses import dataclass

from procflow.application.interfaces.repositories import (
    LineItemRepository,
    MessageRepository,
)
from procflow.domain.entities import ItemMessage
from procflow.domain.exceptions import InvalidInputError


@dataclass(slots=True)
class AddMessage:
    messages: MessageRepository
    items: LineItemRepository

    def __call__(self, line_item_id: int, text: str) -> ItemMessage:
        cleaned = text.strip()
        if not cleaned:
            raise InvalidInputError("Повідомлення не може бути порожнім")
        self.items.get(line_item_id)  # raises if missing
        return self.messages.add(ItemMessage(id=None, line_item_id=line_item_id, text=cleaned))


@dataclass(slots=True)
class DeleteMessage:
    messages: MessageRepository

    def __call__(self, message_id: int) -> None:
        self.messages.delete(message_id)
