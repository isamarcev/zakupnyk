"""Routes for the payer directory (funds and persons with requisites)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from procflow.application.dto import PayerInput
from procflow.application.uow import UnitOfWork
from procflow.presentation.api.deps import get_uow
from procflow.presentation.templating import templates

router = APIRouter()


@router.get("/payers", response_class=HTMLResponse)
def list_payers(request: Request, q: str = "", uow: UnitOfWork = Depends(get_uow)) -> HTMLResponse:
    payers = uow.list_payers(query=q or None)
    return templates.TemplateResponse(
        request, "payers.html", {"payers": payers, "q": q, "active": "payers"}
    )


@router.post("/payers")
def create_payer(
    name: str = Form(""),
    requisites: str = Form(""),
    iban: str = Form(""),
    tax_id: str = Form(""),
    bank: str = Form(""),
    notes: str = Form(""),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    uow.create_payer(
        PayerInput(
            name=name, requisites=requisites, iban=iban, tax_id=tax_id, bank=bank, notes=notes
        )
    )
    return RedirectResponse("/payers", status_code=303)


@router.post("/payers/{payer_id}/update")
def update_payer(
    payer_id: int,
    name: str = Form(""),
    requisites: str = Form(""),
    iban: str = Form(""),
    tax_id: str = Form(""),
    bank: str = Form(""),
    notes: str = Form(""),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    uow.update_payer(
        payer_id,
        PayerInput(
            name=name, requisites=requisites, iban=iban, tax_id=tax_id, bank=bank, notes=notes
        ),
    )
    return RedirectResponse("/payers", status_code=303)


@router.post("/payers/{payer_id}/delete")
def delete_payer(payer_id: int, uow: UnitOfWork = Depends(get_uow)) -> RedirectResponse:
    uow.delete_payer(payer_id)
    return RedirectResponse("/payers", status_code=303)
