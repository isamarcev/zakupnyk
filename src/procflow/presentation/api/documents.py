"""Routes for documents: upload, download, search, delete."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Form, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from procflow.application.dto import AttachDocumentInput
from procflow.application.uow import UnitOfWork
from procflow.domain.entities import DocumentKind
from procflow.presentation.api.deps import get_uow
from procflow.presentation.templating import templates

router = APIRouter()


@router.get("/documents", response_class=HTMLResponse)
def search_documents(
    request: Request, q: str = "", uow: UnitOfWork = Depends(get_uow)
) -> HTMLResponse:
    views = uow.search_documents(text=q or None)
    return templates.TemplateResponse(
        request, "documents.html", {"views": views, "q": q, "active": "documents"}
    )


@router.post("/documents/open-folder")
def open_files_folder(uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Reveal the root files folder in the OS file manager (local run only)."""
    uow.storage.reveal_folder()
    return Response(status_code=204)


async def _attach(
    uow: UnitOfWork,
    *,
    procurement_id: int,
    file: UploadFile,
    title: str,
    kind: str,
    supplier_id: str,
    payer_id: str,
    amount: str,
    doc_date: str,
    note: str,
    line_item_ids: list[int],
) -> None:
    content = await file.read()
    amount_cleaned = amount.strip().replace(",", ".").replace(" ", "")
    uow.attach_document(
        AttachDocumentInput(
            procurement_id=procurement_id,
            supplier_id=int(supplier_id) if supplier_id.strip() else None,
            payer_id=int(payer_id) if payer_id.strip() else None,
            kind=DocumentKind(kind),
            title=title,
            original_name=file.filename or "документ",
            content=content,
            amount=float(amount_cleaned) if amount_cleaned else None,
            doc_date=date.fromisoformat(doc_date) if doc_date.strip() else None,
            note=note,
            line_item_ids=line_item_ids,
        )
    )


@router.post("/items/{item_id}/documents")
async def upload_item_document(
    item_id: int,
    file: UploadFile,
    title: str = Form(""),
    kind: str = Form(DocumentKind.INVOICE.value),
    supplier_id: str = Form(""),
    payer_id: str = Form(""),
    amount: str = Form(""),
    doc_date: str = Form(""),
    note: str = Form(""),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    """Main flow: a document belongs to a specific order position (each position
    may have its own supplier)."""
    item = uow.items.get(item_id)
    await _attach(
        uow,
        procurement_id=item.procurement_id,
        file=file,
        title=title,
        kind=kind,
        supplier_id=supplier_id,
        payer_id=payer_id,
        amount=amount,
        doc_date=doc_date,
        note=note,
        line_item_ids=[item_id],
    )
    return RedirectResponse(f"/procurements/{item.procurement_id}", status_code=303)


@router.post("/procurements/{procurement_id}/documents")
async def upload_document(
    procurement_id: int,
    file: UploadFile,
    title: str = Form(""),
    kind: str = Form(DocumentKind.INVOICE.value),
    supplier_id: str = Form(""),
    payer_id: str = Form(""),
    amount: str = Form(""),
    doc_date: str = Form(""),
    note: str = Form(""),
    line_item_ids: list[int] = Form([]),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    """Secondary flow: a procurement-wide document (e.g. договір на всю закупівлю)."""
    await _attach(
        uow,
        procurement_id=procurement_id,
        file=file,
        title=title,
        kind=kind,
        supplier_id=supplier_id,
        payer_id=payer_id,
        amount=amount,
        doc_date=doc_date,
        note=note,
        line_item_ids=line_item_ids,
    )
    return RedirectResponse(f"/procurements/{procurement_id}", status_code=303)


_INLINE_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".txt"}


@router.get("/documents/{document_id}/file")
def open_document(document_id: int, uow: UnitOfWork = Depends(get_uow)) -> FileResponse:
    """Open the stored file. PDFs/images render inline in the browser tab;
    other formats (xls, docx…) are downloaded since the browser can't show them."""
    document = uow.documents.get(document_id)
    path = uow.storage.absolute_path(document.file_path)
    inline = path.suffix.lower() in _INLINE_SUFFIXES
    disposition = "inline" if inline else "attachment"
    return FileResponse(
        path,
        filename=document.original_name,
        content_disposition_type=disposition,
    )


@router.post("/documents/{document_id}/delete")
def delete_document(document_id: int, uow: UnitOfWork = Depends(get_uow)) -> RedirectResponse:
    procurement_id = uow.documents.get(document_id).procurement_id
    uow.delete_document(document_id)
    return RedirectResponse(f"/procurements/{procurement_id}", status_code=303)
