"""Commands for logistics recipients (delivery templates).

A recipient can be created from a single pasted block: the name is taken from
the first informative line and the phone number is extracted automatically.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from procflow.application.dto import RecipientInput
from procflow.application.interfaces.repositories import RecipientRepository
from procflow.domain.entities import Recipient
from procflow.domain.exceptions import InvalidInputError

# why: телефон у будь-якому форматі (+380 00 111 22 33, 0001112233, …) — 10+ цифр
_PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{8,}\d)")
_NAME_HINT_RE = re.compile(r"отримувач", re.IGNORECASE)


def _looks_like_phone(line: str) -> bool:
    digits = re.sub(r"\D", "", line)
    return len(digits) >= 9


def _normalized(data: RecipientInput) -> tuple[str, RecipientInput]:
    """Derive missing name/phone from the pasted block."""
    block = data.block.strip()
    name = data.name.strip()
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]

    if not name and lines:
        # пропускаємо рядки-мітки ("Отримувач") і телефони — беремо перше справжнє значення
        for ln in lines:
            if _NAME_HINT_RE.fullmatch(ln) or _looks_like_phone(ln):
                continue
            name = ln[:300]
            break
        if not name:
            name = lines[0][:300]
    if not name:
        raise InvalidInputError("Вкажіть отримувача або вставте блок даних")

    phone = data.phone.strip()
    if not phone and block:
        match = _PHONE_RE.search(block)
        phone = match.group(1).strip() if match else ""

    return name, RecipientInput(
        name=name,
        purpose=data.purpose.strip(),
        phone=phone,
        address=data.address.strip(),
        block=block,
        notes=data.notes.strip(),
    )


@dataclass(slots=True)
class CreateRecipient:
    recipients: RecipientRepository

    def __call__(self, data: RecipientInput) -> Recipient:
        name, n = _normalized(data)
        return self.recipients.add(
            Recipient(
                id=None,
                name=name,
                purpose=n.purpose,
                phone=n.phone,
                address=n.address,
                block=n.block,
                notes=n.notes,
            )
        )


@dataclass(slots=True)
class UpdateRecipient:
    recipients: RecipientRepository

    def __call__(self, recipient_id: int, data: RecipientInput) -> Recipient:
        name, n = _normalized(data)
        recipient = self.recipients.get(recipient_id)
        recipient.name = name
        recipient.purpose = n.purpose
        recipient.phone = n.phone
        recipient.address = n.address
        recipient.block = n.block
        recipient.notes = n.notes
        self.recipients.update(recipient)
        return recipient


@dataclass(slots=True)
class DeleteRecipient:
    recipients: RecipientRepository

    def __call__(self, recipient_id: int) -> None:
        self.recipients.get(recipient_id)  # raises if missing
        self.recipients.delete(recipient_id)


@dataclass(slots=True)
class ListRecipients:
    recipients: RecipientRepository

    def __call__(self, *, query: str | None = None) -> list[Recipient]:
        return self.recipients.list_all(query=query)
