"""Document entity: invoices and other purchase paperwork."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum


class DocumentKind(str, Enum):
    """Type of purchase document."""

    INVOICE = "invoice"
    WAYBILL = "waybill"
    CONTRACT = "contract"
    OTHER = "other"

    @property
    def label_uk(self) -> str:
        """Ukrainian display label."""
        return {
            DocumentKind.INVOICE: "Рахунок",
            DocumentKind.WAYBILL: "Накладна",
            DocumentKind.CONTRACT: "Договір",
            DocumentKind.OTHER: "Інше",
        }[self]


@dataclass(slots=True)
class Document:
    """A stored file (PDF/photo/scan) tied to a procurement and a supplier.

    ``file_path`` is relative to the managed files root; the original file is
    copied there on attach so the archive stays self-contained.
    """

    id: int | None
    procurement_id: int
    supplier_id: int | None
    payer_id: int | None
    kind: DocumentKind
    title: str
    file_path: str
    original_name: str
    amount: float | None = None
    doc_date: date | None = None
    note: str = ""
    line_item_ids: list[int] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
