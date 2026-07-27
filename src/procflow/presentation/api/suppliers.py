"""Routes for the supplier directory."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from procflow.application.dto import SupplierInput
from procflow.application.uow import UnitOfWork
from procflow.domain.entities import SupplierSource
from procflow.presentation.api.deps import get_uow
from procflow.presentation.templating import templates

router = APIRouter()


@router.get("/suppliers", response_class=HTMLResponse)
def list_suppliers(
    request: Request, q: str = "", uow: UnitOfWork = Depends(get_uow)
) -> HTMLResponse:
    suppliers = uow.list_suppliers(name_query=q or None)
    return templates.TemplateResponse(
        request,
        "suppliers.html",
        {"suppliers": suppliers, "sources": list(SupplierSource), "q": q, "active": "suppliers"},
    )


@router.post("/suppliers")
def create_supplier(
    name: str = Form(...),
    source: str = Form(...),
    contacts: str = Form(""),
    notes: str = Form(""),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    supplier = uow.create_supplier(
        SupplierInput(name=name, source=SupplierSource(source), contacts=contacts, notes=notes)
    )
    return RedirectResponse(f"/suppliers/{supplier.id}", status_code=303)


@router.get("/suppliers/{supplier_id}", response_class=HTMLResponse)
def supplier_details(
    request: Request, supplier_id: int, uow: UnitOfWork = Depends(get_uow)
) -> HTMLResponse:
    details = uow.get_supplier_details(supplier_id)
    return templates.TemplateResponse(
        request,
        "supplier_detail.html",
        {"d": details, "sources": list(SupplierSource), "active": "suppliers"},
    )


@router.post("/suppliers/{supplier_id}/update")
def update_supplier(
    supplier_id: int,
    name: str = Form(...),
    source: str = Form(...),
    contacts: str = Form(""),
    notes: str = Form(""),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    uow.update_supplier(
        supplier_id,
        SupplierInput(name=name, source=SupplierSource(source), contacts=contacts, notes=notes),
    )
    return RedirectResponse(f"/suppliers/{supplier_id}", status_code=303)
