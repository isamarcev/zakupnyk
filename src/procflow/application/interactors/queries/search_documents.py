"""Query: search documents across procurements and suppliers."""

from __future__ import annotations

from dataclasses import dataclass

from procflow.application.dto import DocumentView
from procflow.application.interfaces.repositories import DocumentRepository


@dataclass(slots=True)
class SearchDocuments:
    documents: DocumentRepository

    def __call__(
        self,
        *,
        text: str | None = None,
        procurement_id: int | None = None,
        supplier_id: int | None = None,
    ) -> list[DocumentView]:
        return self.documents.search(
            text=text, procurement_id=procurement_id, supplier_id=supplier_id
        )
