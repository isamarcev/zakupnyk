"""Payer entity: who pays for the purchase (fund, volunteer, person)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Payer:
    """Payment requisites used when sending money to a supplier.

    ``requisites`` keeps the full pasted block verbatim (юр. адреса, тел., …) —
    that is what gets copied and sent. ``name`` is the account holder
    (отримувач), ``iban``/``tax_id`` (ІПН/ЄДРПОУ) are extracted for search
    and one-click copy.
    """

    id: int | None
    name: str
    requisites: str = ""
    iban: str = ""
    tax_id: str = ""
    bank: str = ""
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def copy_text(self) -> str:
        """The block to copy: verbatim requisites if present, else composed fields."""
        if self.requisites:
            return self.requisites
        lines = [f"Отримувач: {self.name}"]
        if self.iban:
            lines.append(f"IBAN: {self.iban}")
        if self.tax_id:
            lines.append(f"ІПН/ЄДРПОУ: {self.tax_id}")
        if self.bank:
            lines.append(f"Банк: {self.bank}")
        return "\n".join(lines)
