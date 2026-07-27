"""Document repository interface."""

from __future__ import annotations

from typing import Protocol

from procflow.application.dto import DocumentView
from procflow.domain.entities import Document


class DocumentRepository(Protocol):
    def add(self, document: Document) -> Document:
        """Persist a new document record. Returns it with ``id`` populated."""
        ...

    def get(self, document_id: int) -> Document:
        """Fetch by id or raise DocumentNotFoundError."""
        ...

    def search(
        self,
        *,
        text: str | None = None,
        procurement_id: int | None = None,
        supplier_id: int | None = None,
    ) -> list[DocumentView]:
        """Return documents (newest first) filtered by text/procurement/supplier."""
        ...

    def delete(self, document_id: int) -> None:
        """Remove the document record (file removal is the use-case's job)."""
        ...
