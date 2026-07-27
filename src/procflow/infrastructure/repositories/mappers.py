"""Row ↔ entity mappers shared by repositories."""

from __future__ import annotations

from procflow.domain.entities import (
    Document,
    DocumentKind,
    ItemMessage,
    ItemStage,
    LineItem,
    Offer,
    Payer,
    Procurement,
    ProcurementStatus,
    Recipient,
    Supplier,
    SupplierSource,
)
from procflow.infrastructure.database import (
    DocumentRow,
    LineItemRow,
    MessageRow,
    OfferRow,
    PayerRow,
    ProcurementRow,
    RecipientRow,
    SupplierRow,
)


def procurement_from_row(row: ProcurementRow) -> Procurement:
    return Procurement(
        id=row.id,
        name=row.name,
        description=row.description,
        status=ProcurementStatus(row.status),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def line_item_from_row(row: LineItemRow) -> LineItem:
    return LineItem(
        id=row.id,
        procurement_id=row.procurement_id,
        name=row.name,
        specification=row.specification,
        qty_required=row.qty_required,
        qty_ordered=row.qty_ordered,
        qty_in_progress=row.qty_in_progress,
        unit_price=row.unit_price,
        stage=ItemStage(row.stage),
        created_at=row.created_at,
    )


def message_from_row(row: MessageRow) -> ItemMessage:
    return ItemMessage(
        id=row.id,
        line_item_id=row.line_item_id,
        text=row.text,
        created_at=row.created_at,
    )


def supplier_from_row(row: SupplierRow) -> Supplier:
    return Supplier(
        id=row.id,
        name=row.name,
        source=SupplierSource(row.source),
        contacts=row.contacts,
        notes=row.notes,
        created_at=row.created_at,
    )


def offer_from_row(row: OfferRow) -> Offer:
    return Offer(
        id=row.id,
        line_item_id=row.line_item_id,
        supplier_id=row.supplier_id,
        url=row.url,
        price=row.price,
        note=row.note,
        created_at=row.created_at,
    )


def payer_from_row(row: PayerRow) -> Payer:
    return Payer(
        id=row.id,
        name=row.name,
        requisites=row.requisites,
        iban=row.iban,
        tax_id=row.tax_id,
        bank=row.bank,
        notes=row.notes,
        created_at=row.created_at,
    )


def recipient_from_row(row: RecipientRow) -> Recipient:
    return Recipient(
        id=row.id,
        name=row.name,
        purpose=row.purpose,
        phone=row.phone,
        address=row.address,
        block=row.block,
        notes=row.notes,
        created_at=row.created_at,
    )


def document_from_row(row: DocumentRow) -> Document:
    return Document(
        id=row.id,
        procurement_id=row.procurement_id,
        supplier_id=row.supplier_id,
        payer_id=row.payer_id,
        kind=DocumentKind(row.kind),
        title=row.title,
        file_path=row.file_path,
        original_name=row.original_name,
        amount=row.amount,
        doc_date=row.doc_date,
        note=row.note,
        line_item_ids=[link.line_item_id for link in row.item_links],
        created_at=row.created_at,
    )
