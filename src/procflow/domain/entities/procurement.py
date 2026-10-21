"""Procurement aggregate: a purchasing project with line items."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ProcurementStatus(str, Enum):
    """Lifecycle of a procurement project."""

    DRAFT = "draft"
    ACTIVE = "active"
    DONE = "done"

    @property
    def label_uk(self) -> str:
        """Ukrainian display label."""
        return {
            ProcurementStatus.DRAFT: "Чернетка",
            ProcurementStatus.ACTIVE: "В роботі",
            ProcurementStatus.DONE: "Завершена",
        }[self]


@dataclass(slots=True)
class Procurement:
    """A purchasing project (e.g. one ground-station kit order)."""

    id: int | None
    name: str
    description: str
    status: ProcurementStatus
    created_at: datetime
    updated_at: datetime


class ItemStage(str, Enum):
    """Workflow stage of a single order position (independent of quantities)."""

    NEW = "new"
    AWAITING_INVOICE = "awaiting_invoice"
    SENT_FOR_PAYMENT = "sent_for_payment"
    PAID = "paid"
    RECEIVED = "received"
    CLOSED = "closed"
    BLOCKED = "blocked"

    @property
    def label_uk(self) -> str:
        """Ukrainian display label."""
        return {
            ItemStage.NEW: "Нове",
            ItemStage.AWAITING_INVOICE: "Очікую рахунок",
            ItemStage.SENT_FOR_PAYMENT: "Передано на оплату",
            ItemStage.PAID: "Оплачено, очікую поставку",
            ItemStage.RECEIVED: "Отримано",
            ItemStage.CLOSED: "Закрито (документи)",
            ItemStage.BLOCKED: "Проблема / скасовано",
        }[self]


@dataclass(slots=True)
class LineItem:
    """One required item inside a procurement.

    Quantities: ``qty_required`` is the target; ``qty_ordered`` is paid/ordered;
    ``qty_in_progress`` is being negotiated or shipped. ``stage`` tracks the
    paperwork workflow (рахунок → оплата → поставка → закриття). ``module`` —
    інженерна група («що це»), ``order_id`` — комерційна («чим одним рахунком
    купуємо»); осі незалежні, обидві опційні.
    """

    id: int | None
    procurement_id: int
    name: str
    specification: str
    qty_required: float
    qty_ordered: float = 0.0
    qty_in_progress: float = 0.0
    unit_price: float | None = None
    stage: ItemStage = ItemStage.NEW
    module: str | None = None
    order_id: int | None = None
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def total_price(self) -> float:
        """Expected total cost for the required quantity."""
        return (self.unit_price or 0.0) * self.qty_required

    @property
    def is_complete(self) -> bool:
        """True when the ordered quantity covers the requirement."""
        return self.qty_required > 0 and self.qty_ordered >= self.qty_required
