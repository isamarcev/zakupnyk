"""SQLAlchemy implementation of the document repository."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from procflow.application.dto import DocumentView
from procflow.domain.entities import Document
from procflow.domain.exceptions import DocumentNotFoundError
from procflow.infrastructure.database import (
    DocumentItemLinkRow,
    DocumentRow,
    PayerRow,
    ProcurementRow,
    SupplierRow,
)
from procflow.infrastructure.repositories.mappers import document_from_row


@dataclass(slots=True)
class SqlDocumentRepository:
    session: Session

    def add(self, document: Document) -> Document:
        row = DocumentRow(
            procurement_id=document.procurement_id,
            supplier_id=document.supplier_id,
            payer_id=document.payer_id,
            kind=document.kind.value,
            title=document.title,
            file_path=document.file_path,
            original_name=document.original_name,
            amount=document.amount,
            doc_date=document.doc_date,
            note=document.note,
            order_id=document.order_id,
            created_at=document.created_at,
        )
        self.session.add(row)
        self.session.flush()
        for item_id in document.line_item_ids:
            self.session.add(DocumentItemLinkRow(document_id=row.id, line_item_id=item_id))
        self.session.flush()
        document.id = row.id
        return document

    def get(self, document_id: int) -> Document:
        row = self.session.get(DocumentRow, document_id)
        if row is None:
            raise DocumentNotFoundError(f"Документ #{document_id} не знайдено")
        return document_from_row(row)

    def search(
        self,
        *,
        text: str | None = None,
        procurement_id: int | None = None,
        supplier_id: int | None = None,
    ) -> list[DocumentView]:
        stmt = (
            select(DocumentRow, ProcurementRow.name, SupplierRow.name, PayerRow.name)
            .join(ProcurementRow, DocumentRow.procurement_id == ProcurementRow.id)
            .outerjoin(SupplierRow, DocumentRow.supplier_id == SupplierRow.id)
            .outerjoin(PayerRow, DocumentRow.payer_id == PayerRow.id)
            .order_by(DocumentRow.created_at.desc())
        )
        if procurement_id is not None:
            stmt = stmt.where(DocumentRow.procurement_id == procurement_id)
        if supplier_id is not None:
            stmt = stmt.where(DocumentRow.supplier_id == supplier_id)
        if text:
            pattern = f"%{text}%"
            stmt = stmt.where(
                or_(
                    DocumentRow.title.ilike(pattern),
                    DocumentRow.note.ilike(pattern),
                    DocumentRow.original_name.ilike(pattern),
                    ProcurementRow.name.ilike(pattern),
                    SupplierRow.name.ilike(pattern),
                )
            )
        return [
            DocumentView(
                document=document_from_row(doc),
                procurement_name=proc_name,
                supplier_name=supp_name,
                payer_name=payer_name,
            )
            for doc, proc_name, supp_name, payer_name in self.session.execute(stmt)
        ]

    def delete(self, document_id: int) -> None:
        row = self.session.get(DocumentRow, document_id)
        if row is None:
            raise DocumentNotFoundError(f"Документ #{document_id} не знайдено")
        self.session.delete(row)
        self.session.flush()
