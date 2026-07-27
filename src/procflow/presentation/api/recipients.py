"""Routes for the logistics recipients directory (delivery templates)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from procflow.application.dto import RecipientInput
from procflow.application.uow import UnitOfWork
from procflow.presentation.api.deps import get_uow
from procflow.presentation.templating import templates

router = APIRouter()


@router.get("/recipients", response_class=HTMLResponse)
def list_recipients(
    request: Request, q: str = "", uow: UnitOfWork = Depends(get_uow)
) -> HTMLResponse:
    recipients = uow.list_recipients(query=q or None)
    return templates.TemplateResponse(
        request, "recipients.html", {"recipients": recipients, "q": q, "active": "recipients"}
    )


@router.post("/recipients")
def create_recipient(
    name: str = Form(""),
    purpose: str = Form(""),
    phone: str = Form(""),
    address: str = Form(""),
    block: str = Form(""),
    notes: str = Form(""),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    uow.create_recipient(
        RecipientInput(
            name=name, purpose=purpose, phone=phone, address=address, block=block, notes=notes
        )
    )
    return RedirectResponse("/recipients", status_code=303)


@router.post("/recipients/{recipient_id}/update")
def update_recipient(
    recipient_id: int,
    name: str = Form(""),
    purpose: str = Form(""),
    phone: str = Form(""),
    address: str = Form(""),
    block: str = Form(""),
    notes: str = Form(""),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    uow.update_recipient(
        recipient_id,
        RecipientInput(
            name=name, purpose=purpose, phone=phone, address=address, block=block, notes=notes
        ),
    )
    return RedirectResponse("/recipients", status_code=303)


@router.post("/recipients/{recipient_id}/delete")
def delete_recipient(recipient_id: int, uow: UnitOfWork = Depends(get_uow)) -> RedirectResponse:
    uow.delete_recipient(recipient_id)
    return RedirectResponse("/recipients", status_code=303)
