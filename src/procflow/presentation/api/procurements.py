"""Routes for procurements and their line items."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from procflow.application.dto import (
    CreateProcurementInput,
    LineItemInput,
    OfferInput,
    SupplierInput,
    UpdateProcurementInput,
)
from procflow.application.uow import UnitOfWork
from procflow.domain.entities import (
    DocumentKind,
    ItemStage,
    ProcurementStatus,
    SupplierSource,
)
from procflow.domain.exceptions import InvalidInputError
from procflow.presentation.api.deps import get_uow
from procflow.presentation.templating import templates

router = APIRouter()


def _parse_optional_float(raw: str) -> float | None:
    cleaned = raw.strip().replace(",", ".").replace(" ", "")
    return float(cleaned) if cleaned else None


@router.get("/", response_class=HTMLResponse)
def home() -> RedirectResponse:
    return RedirectResponse("/procurements", status_code=302)


@router.get("/procurements", response_class=HTMLResponse)
def list_procurements(request: Request, uow: UnitOfWork = Depends(get_uow)) -> HTMLResponse:
    summaries = uow.list_procurements()
    return templates.TemplateResponse(
        request,
        "procurements.html",
        {"summaries": summaries, "statuses": list(ProcurementStatus), "active": "procurements"},
    )


@router.post("/procurements")
def create_procurement(
    name: str = Form(...),
    description: str = Form(""),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    procurement = uow.create_procurement(CreateProcurementInput(name=name, description=description))
    return RedirectResponse(f"/procurements/{procurement.id}", status_code=303)


@router.get("/procurements/{procurement_id}", response_class=HTMLResponse)
def procurement_details(
    request: Request,
    procurement_id: int,
    stage: list[str] = Query([]),
    uow: UnitOfWork = Depends(get_uow),
) -> HTMLResponse:
    details = uow.get_procurement_details(procurement_id)
    suppliers = uow.list_suppliers()
    payers = uow.list_payers()

    stage_counts = dict.fromkeys(ItemStage, 0)
    for view in details.items:
        stage_counts[view.item.stage] += 1
    selected_stages = {ItemStage(s) for s in stage if s}
    visible_items = [
        v for v in details.items if not selected_stages or v.item.stage in selected_stages
    ]
    stage_links = {st: _stage_toggle_link(procurement_id, selected_stages, st) for st in ItemStage}
    return templates.TemplateResponse(
        request,
        "procurement_detail.html",
        {
            "d": details,
            "visible_items": visible_items,
            "selected_stages": selected_stages,
            "stage_links": stage_links,
            "stage_counts": stage_counts,
            "stages": list(ItemStage),
            "suppliers": suppliers,
            "payers": payers,
            "statuses": list(ProcurementStatus),
            "kinds": list(DocumentKind),
            "sources": list(SupplierSource),
            "active": "procurements",
        },
    )


@router.post("/procurements/{procurement_id}/open-folder")
def open_procurement_folder(
    procurement_id: int, uow: UnitOfWork = Depends(get_uow)
) -> Response:
    """Reveal the procurement's document folder in the OS file manager (local run only)."""
    procurement = uow.procurements.get(procurement_id)
    uow.storage.reveal_folder(procurement.name)
    return Response(status_code=204)


def _stage_toggle_link(procurement_id: int, selected: set[ItemStage], toggled: ItemStage) -> str:
    """Chip href: clicking a stage chip adds/removes it from the multi-select filter."""
    stages = [st for st in ItemStage if (st in selected) != (st is toggled)]
    query = "&".join(f"stage={st.value}" for st in stages)
    return f"/procurements/{procurement_id}" + (f"?{query}" if query else "")


@router.post("/procurements/{procurement_id}/update")
def update_procurement(
    procurement_id: int,
    name: str = Form(...),
    description: str = Form(""),
    status: str = Form(...),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    uow.update_procurement(
        UpdateProcurementInput(
            procurement_id=procurement_id,
            name=name,
            description=description,
            status=ProcurementStatus(status),
        )
    )
    return RedirectResponse(f"/procurements/{procurement_id}", status_code=303)


@router.post("/procurements/{procurement_id}/delete")
def delete_procurement(procurement_id: int, uow: UnitOfWork = Depends(get_uow)) -> RedirectResponse:
    uow.delete_procurement(procurement_id)
    return RedirectResponse("/procurements", status_code=303)


@router.post("/procurements/{procurement_id}/items")
def add_line_item(
    procurement_id: int,
    name: str = Form(...),
    specification: str = Form(""),
    qty_required: str = Form("0"),
    unit_price: str = Form(""),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    uow.add_line_item(
        procurement_id,
        LineItemInput(
            name=name,
            specification=specification,
            qty_required=_parse_optional_float(qty_required) or 0.0,
            unit_price=_parse_optional_float(unit_price),
        ),
    )
    return RedirectResponse(f"/procurements/{procurement_id}", status_code=303)


@router.post("/items/{item_id}/update")
def update_line_item(
    item_id: int,
    name: str = Form(...),
    specification: str = Form(""),
    qty_required: str = Form("0"),
    qty_ordered: str = Form("0"),
    qty_in_progress: str = Form("0"),
    unit_price: str = Form(""),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    item = uow.update_line_item(
        item_id,
        LineItemInput(
            name=name,
            specification=specification,
            qty_required=_parse_optional_float(qty_required) or 0.0,
            qty_ordered=_parse_optional_float(qty_ordered) or 0.0,
            qty_in_progress=_parse_optional_float(qty_in_progress) or 0.0,
            unit_price=_parse_optional_float(unit_price),
        ),
    )
    return RedirectResponse(f"/procurements/{item.procurement_id}", status_code=303)


@router.get("/items/{item_id}", response_class=HTMLResponse)
def line_item_details(
    request: Request, item_id: int, uow: UnitOfWork = Depends(get_uow)
) -> HTMLResponse:
    details = uow.get_line_item_details(item_id)
    return templates.TemplateResponse(
        request,
        "line_item_detail.html",
        {
            "d": details,
            "suppliers": uow.list_suppliers(),
            "stages": list(ItemStage),
            "active": "procurements",
        },
    )


@router.post("/items/{item_id}/messages")
def add_message(
    item_id: int, text: str = Form(...), uow: UnitOfWork = Depends(get_uow)
) -> RedirectResponse:
    uow.add_message(item_id, text)
    return RedirectResponse(f"/items/{item_id}", status_code=303)


@router.post("/messages/{message_id}/delete")
def delete_message(
    message_id: int, item_id: int = Form(...), uow: UnitOfWork = Depends(get_uow)
) -> RedirectResponse:
    uow.delete_message(message_id)
    return RedirectResponse(f"/items/{item_id}", status_code=303)


@router.post("/items/{item_id}/stage")
def set_item_stage(
    item_id: int,
    stage: str = Form(...),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    item = uow.set_item_stage(item_id, ItemStage(stage))
    return RedirectResponse(f"/procurements/{item.procurement_id}", status_code=303)


@router.post("/items/{item_id}/delete")
def delete_line_item(item_id: int, uow: UnitOfWork = Depends(get_uow)) -> RedirectResponse:
    procurement_id = uow.items.get(item_id).procurement_id
    uow.delete_line_item(item_id)
    return RedirectResponse(f"/procurements/{procurement_id}", status_code=303)


@router.post("/items/{item_id}/offers")
def add_offer(
    item_id: int,
    supplier_id: str = Form(""),
    new_supplier_name: str = Form(""),
    new_supplier_source: str = Form(SupplierSource.DISTRIBUTOR.value),
    url: str = Form(""),
    price: str = Form(""),
    note: str = Form(""),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    procurement_id = uow.items.get(item_id).procurement_id
    resolved_supplier_id = _resolve_supplier(
        uow, supplier_id, new_supplier_name, new_supplier_source
    )
    uow.add_offer(
        OfferInput(
            line_item_id=item_id,
            supplier_id=resolved_supplier_id,
            url=url,
            price=_parse_optional_float(price),
            note=note,
        )
    )
    return RedirectResponse(f"/procurements/{procurement_id}", status_code=303)


def _resolve_supplier(
    uow: UnitOfWork, supplier_id: str, new_supplier_name: str, new_supplier_source: str
) -> int:
    """Use the selected supplier or create a named one on the fly (deduped by name)."""
    if new_supplier_name.strip():
        existing = uow.suppliers.get_by_name(new_supplier_name.strip())
        if existing is not None:
            assert existing.id is not None
            return existing.id
        created = uow.create_supplier(
            SupplierInput(name=new_supplier_name, source=SupplierSource(new_supplier_source))
        )
        assert created.id is not None
        return created.id
    if supplier_id.strip():
        return int(supplier_id)
    raise InvalidInputError("Оберіть постачальника або введіть назву нового")


@router.post("/offers/{offer_id}/delete")
def delete_offer(offer_id: int, uow: UnitOfWork = Depends(get_uow)) -> RedirectResponse:
    offer = uow.offers.get(offer_id)
    procurement_id = uow.items.get(offer.line_item_id).procurement_id
    uow.delete_offer(offer_id)
    return RedirectResponse(f"/procurements/{procurement_id}", status_code=303)
