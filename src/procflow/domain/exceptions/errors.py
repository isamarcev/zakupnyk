"""Domain-level exceptions.

Use-cases raise these; presentation layer maps them to HTTP responses.
Never raise generic Exception or framework-specific errors from domain/application.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain errors.

    Subclasses override ``code`` (stable machine-readable identifier) and
    ``status`` (HTTP status the presentation layer should map to).
    """

    code: str = "domain_error"
    status: int = 400

    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ProcurementNotFoundError(DomainError):
    code = "procurement_not_found"
    status = 404


class LineItemNotFoundError(DomainError):
    code = "line_item_not_found"
    status = 404


class MessageNotFoundError(DomainError):
    code = "message_not_found"
    status = 404


class SupplierNotFoundError(DomainError):
    code = "supplier_not_found"
    status = 404


class SupplierOrderNotFoundError(DomainError):
    code = "supplier_order_not_found"
    status = 404


class OfferNotFoundError(DomainError):
    code = "offer_not_found"
    status = 404


class DocumentNotFoundError(DomainError):
    code = "document_not_found"
    status = 404


class PayerNotFoundError(DomainError):
    code = "payer_not_found"
    status = 404


class RecipientNotFoundError(DomainError):
    code = "recipient_not_found"
    status = 404


class InvalidInputError(DomainError):
    code = "invalid_input"
    status = 422


class StorageError(DomainError):
    """Raised when the filesystem-backed storage fails (I/O issue, missing file)."""

    code = "storage_error"
    status = 500


class XlsxImportError(DomainError):
    """Raised when an Excel needs-list cannot be parsed."""

    code = "xlsx_import_error"
    status = 422
