"""Routes for documents: upload, download, search, delete."""

from __future__ import annotations

from datetime import date
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from procflow.application.dto import AttachDocumentInput
from procflow.application.interactors.queries.group_items import GROUP_MODES
from procflow.application.uow import UnitOfWork
from procflow.domain.entities import DocumentKind, ItemStage
from procflow.infrastructure.archive import build_zip
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
    order_id: int | None = None,
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
            order_id=order_id,
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


@router.post("/orders/{order_id}/documents")
async def upload_order_document(
    order_id: int,
    file: UploadFile,
    title: str = Form(""),
    kind: str = Form(DocumentKind.INVOICE.value),
    payer_id: str = Form(""),
    amount: str = Form(""),
    doc_date: str = Form(""),
    note: str = Form(""),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    """Один рахунок на все замовлення: привʼязується до кожної його позиції.

    why: раніше той самий файл вантажили по разу на позицію (4 копії одного
    рахунка в архіві) — тепер завантаження одне, а в рядках позицій він видний
    через ті самі звʼязки document_item_links.
    """
    order = uow.orders.get(order_id)
    item_ids = [
        i.id
        for i in uow.items.list_for_procurement(order.procurement_id)
        if i.order_id == order_id and i.id is not None
    ]
    await _attach(
        uow,
        procurement_id=order.procurement_id,
        file=file,
        title=title,
        kind=kind,
        supplier_id=str(order.supplier_id or ""),
        payer_id=payer_id,
        amount=amount,
        doc_date=doc_date,
        note=note,
        line_item_ids=item_ids,
        order_id=order_id,
    )
    return RedirectResponse(f"/procurements/{order.procurement_id}", status_code=303)


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


@router.get("/procurements/{procurement_id}/documents.zip")
def export_documents(
    procurement_id: int,
    stage: list[str] = Query([]),
    order: int | None = Query(None),
    item: list[int] = Query([]),
    kind: list[str] = Query([]),
    group: str = Query("module"),
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    """Архів документів по тому, що зараз відфільтровано/вибрано на сторінці."""
    bundle = uow.export_documents(
        procurement_id,
        stages={ItemStage(s) for s in stage if s},
        order_id=order,
        item_ids=item,
        kinds={DocumentKind(k) for k in kind if k},
        group=group if group in GROUP_MODES else "module",
    )
    content = build_zip(bundle, uow.storage.absolute_path)
    # RFC 5987: кирилиця в імені файлу лишається читабельною в браузері
    disposition = f"attachment; filename*=UTF-8''{quote(bundle.filename)}"
    return Response(
        content=content,
        media_type="application/zip",
        headers={"content-disposition": disposition},
    )


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
