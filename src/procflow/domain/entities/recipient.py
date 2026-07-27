"""Recipient entity: a reusable delivery/logistics template.

Mirrors Payer: ``block`` keeps the pasted text verbatim (that is what gets
copied and sent to a courier), while name/phone/address are extracted for
search and quick copy. ``purpose`` is a free label ("Для доставки",
"Для документів"…) so templates can be grouped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

# why: телефон у будь-якому форматі (+380 00 111 22 33, 0001112233…) — 10+ знаків
_PHONE_RE = re.compile(r"\+?\d[\d\s().-]{8,}\d")


@dataclass(slots=True)
class Recipient:
    """A saved logistics recipient (Нова Пошта / courier delivery details)."""

    id: int | None
    name: str
    purpose: str = ""
    phone: str = ""
    address: str = ""
    block: str = ""
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def phones(self) -> list[str]:
        """All distinct phone numbers: explicit field + every match in the block.

        Один шаблон може містити кілька отримувачів (для доставки і для
        документів), тож повертаємо всі знайдені номери — для окремих кнопок.
        """
        result: list[str] = []
        if self.phone:
            result.append(self.phone.strip())
        for match in _PHONE_RE.finditer(self.block):
            phone = match.group(0).strip()
            if phone not in result:
                result.append(phone)
        return result

    @property
    def copy_text(self) -> str:
        """The block to copy: verbatim text if present, else composed fields."""
        if self.block:
            return self.block
        lines = [f"Отримувач: {self.name}"]
        if self.phone:
            lines.append(f"Телефон отримувача: {self.phone}")
        if self.address:
            lines.append(f"Адреса: {self.address}")
        return "\n".join(lines)
