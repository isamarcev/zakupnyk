"""Application-level DTOs: inputs for commands and read models for queries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from procflow.domain.entities import (
    Document,
    DocumentKind,
    ItemMessage,
    ItemStage,
    LineItem,
    Offer,
    Procurement,
    ProcurementStatus,
    Supplier,
    SupplierOrder,
    SupplierSource,
)

# ---------------------------------------------------------------- command inputs


@dataclass(slots=True)
class CreateProcurementInput:
    name: str
    description: str = ""


@dataclass(slots=True)
class UpdateProcurementInput:
    procurement_id: int
    name: str
    description: str
    status: ProcurementStatus


@dataclass(slots=True)
class LineItemInput:
    """Shared payload for creating/updating a line item."""

    name: str
    specification: str = ""
    qty_required: float = 0.0
    qty_ordered: float = 0.0
    qty_in_progress: float = 0.0
    unit_price: float | None = None
    module: str | None = None


@dataclass(slots=True)
class SupplierOrderInput:
    """Замовлення: назва + продавець (наявний або новий, створюється на льоту)."""

    title: str = ""
    supplier_id: int | None = None
    new_supplier_name: str = ""
    new_supplier_source: SupplierSource = SupplierSource.DISTRIBUTOR
    note: str = ""


@dataclass(slots=True)
class SupplierInput:
    name: str
    source: SupplierSource
    contacts: str = ""
    notes: str = ""


@dataclass(slots=True)
class OfferInput:
    line_item_id: int
    supplier_id: int
    url: str = ""
    price: float | None = None
    note: str = ""


@dataclass(slots=True)
class PayerInput:
    """Payer payload; ``name`` may be empty when ``requisites`` is pasted —
    the command derives it from the first line."""

    name: str = ""
    requisites: str = ""
    iban: str = ""
    tax_id: str = ""
    bank: str = ""
    notes: str = ""


@dataclass(slots=True)
class RecipientInput:
    """Recipient payload; ``name`` may be empty when ``block`` is pasted —
    the command derives it from the first informative line."""

    name: str = ""
    purpose: str = ""
    phone: str = ""
    address: str = ""
    block: str = ""
    notes: str = ""


@dataclass(slots=True)
class AttachDocumentInput:
    procurement_id: int
    supplier_id: int | None
    kind: DocumentKind
    title: str
    original_name: str
    content: bytes
    payer_id: int | None = None
    amount: float | None = None
    doc_date: date | None = None
    note: str = ""
    order_id: int | None = None
    line_item_ids: list[int] = field(default_factory=list)


# ---------------------------------------------------------------- read models


@dataclass(slots=True)
class ProcurementSummary:
    """List-view row: procurement with aggregate progress and cost."""

    procurement: Procurement
    items_total: int
    items_complete: int
    cost_total: float
    documents_count: int


@dataclass(slots=True)
class LineItemView:
    """Line item with its offers (offer + supplier pairs) and last message."""

    item: LineItem
    offers: list[tuple[Offer, Supplier]] = field(default_factory=list)
    last_message: ItemMessage | None = None
    stage_since: datetime | None = None
    """Коли позиція перейшла в поточну стадію; None — переходу не зафіксовано."""
    order: SupplierOrder | None = None
    """Замовлення, у складі якого купується позиція; None — купується окремо."""


@dataclass(slots=True)
class StageStep:
    """One step of a line item's stage timeline; ``at`` is None when unknown."""

    stage: ItemStage
    at: datetime | None


@dataclass(slots=True)
class LineItemDetails:
    """Full single-position view: item, offers, documents, message thread."""

    item: LineItem
    procurement: Procurement
    offers: list[tuple[Offer, Supplier]]
    documents: list[DocumentView]
    messages: list[ItemMessage]
    stage_timeline: list[StageStep] = field(default_factory=list)
    order: SupplierOrder | None = None
    order_supplier: Supplier | None = None


@dataclass(slots=True)
class OrderView:
    """Замовлення з його позиціями і документами; агрегати — похідні."""

    order: SupplierOrder
    supplier: Supplier | None
    items: list[LineItemView] = field(default_factory=list)
    documents: list[DocumentView] = field(default_factory=list)

    @property
    def cost_total(self) -> float:
        """Кошторис замовлення за цінами позицій."""
        return sum(v.item.total_price for v in self.items)

    @property
    def invoiced_total(self) -> float | None:
        """Сума за документами; None — жодної суми не вказано."""
        amounts = [v.document.amount for v in self.documents if v.document.amount is not None]
        return sum(amounts) if amounts else None

    @property
    def stage(self) -> ItemStage | None:
        """Спільна стадія всіх позицій; None — стадії різні («змішана»)."""
        stages = {v.item.stage for v in self.items}
        return stages.pop() if len(stages) == 1 else None


@dataclass(slots=True)
class ItemGroup:
    """Блок таблиці позицій: заголовок + свої позиції.

    Одна структура на дві осі групування — модуль і замовлення, тож шаблон,
    копія специфікації та експорт не знають різниці.
    """

    key: str
    label: str
    icon: str
    items: list[LineItemView] = field(default_factory=list)
    order: OrderView | None = None

    @property
    def cost_total(self) -> float:
        return sum(v.item.total_price for v in self.items)


@dataclass(slots=True)
class ProcurementDetails:
    procurement: Procurement
    items: list[LineItemView]
    documents: list[DocumentView]
    cost_total: float
    orders: list[OrderView] = field(default_factory=list)


@dataclass(slots=True)
class DocumentView:
    """Document joined with its procurement/supplier/payer names for display."""

    document: Document
    procurement_name: str
    supplier_name: str | None
    payer_name: str | None = None


@dataclass(slots=True)
class ExportEntry:
    """Один файл в архіві: імʼя всередині і шлях у сховищі."""

    arcname: str
    file_path: str


@dataclass(slots=True)
class ExportBundle:
    """Матеріал для архіву документів: файли + текстовий перелік."""

    filename: str
    entries: list[ExportEntry]
    listing: str


@dataclass(slots=True)
class SupplierDetails:
    supplier: Supplier
    offers: list[tuple[Offer, LineItem]]
    documents: list[DocumentView]


# ---------------------------------------------------------------- xlsx import


@dataclass(slots=True)
class ImportedOffer:
    source: SupplierSource
    url: str
    price: float | None


@dataclass(slots=True)
class ImportedRow:
    name: str
    specification: str
    qty_required: float
    qty_ordered: float
    qty_in_progress: float
    unit_price: float | None
    offers: list[ImportedOffer] = field(default_factory=list)


@dataclass(slots=True)
class ImportedSheet:
    title: str
    rows: list[ImportedRow] = field(default_factory=list)
