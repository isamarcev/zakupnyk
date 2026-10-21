"""Commands for documents: attach a file to a procurement, delete it."""

from __future__ import annotations

from dataclasses import dataclass

from procflow.application.dto import AttachDocumentInput
from procflow.application.interfaces import FileStorage
from procflow.application.interfaces.repositories import (
    DocumentRepository,
    PayerRepository,
    ProcurementRepository,
    SupplierRepository,
)
from procflow.domain.entities import Document
from procflow.domain.exceptions import InvalidInputError


@dataclass(slots=True)
class AttachDocument:
    documents: DocumentRepository
    procurements: ProcurementRepository
    suppliers: SupplierRepository
    payers: PayerRepository
    storage: FileStorage

    def __call__(self, cmd: AttachDocumentInput) -> Document:
        if not cmd.content:
            raise InvalidInputError("Файл порожній")
        procurement = self.procurements.get(cmd.procurement_id)
        supplier_name: str | None = None
        if cmd.supplier_id is not None:
            supplier_name = self.suppliers.get(cmd.supplier_id).name
        if cmd.payer_id is not None:
            self.payers.get(cmd.payer_id)  # raises if missing

        relative_path = self.storage.save(
            procurement_name=procurement.name,
            supplier_name=supplier_name,
            filename=cmd.original_name,
            content=cmd.content,
        )
        return self.documents.add(
            Document(
                id=None,
                procurement_id=cmd.procurement_id,
                supplier_id=cmd.supplier_id,
                payer_id=cmd.payer_id,
                kind=cmd.kind,
                title=cmd.title.strip() or cmd.original_name,
                file_path=relative_path,
                original_name=cmd.original_name,
                amount=cmd.amount,
                doc_date=cmd.doc_date,
                note=cmd.note.strip(),
                order_id=cmd.order_id,
                line_item_ids=cmd.line_item_ids,
            )
        )


@dataclass(slots=True)
class DeleteDocument:
    documents: DocumentRepository
    storage: FileStorage

    def __call__(self, document_id: int) -> None:
        document = self.documents.get(document_id)
        self.documents.delete(document_id)
        self.storage.remove(document.file_path)
