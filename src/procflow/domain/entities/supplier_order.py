"""Supplier order: positions bought together from one supplier by one invoice."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class SupplierOrder:
    """Комерційне групування позицій усередині закупівлі.

    Модуль відповідає на питання «що це» (інженерна розбивка з xlsx), замовлення —
    «як купуємо»: набір позицій, які їдуть одним рахунком від одного продавця.
    Осі ортогональні: одне замовлення часто перетинає кілька модулів.
    """

    id: int | None
    procurement_id: int
    title: str
    supplier_id: int | None = None
    note: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    def display_title(self) -> str:
        """Назва для UI; порожня назва падає назад на «Замовлення #id»."""
        return self.title.strip() or f"Замовлення #{self.id}"
