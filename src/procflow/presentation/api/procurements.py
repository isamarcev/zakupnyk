"""Routes for procurements and their line items."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from procflow.application.dto import (
    CreateProcurementInput,
    LineItemInput,
    OfferInput,
    UpdateProcurementInput,
)
from procflow.application.interactors.queries.group_items import (
    GROUP_MODES,
    build_groups,
    sort_for_orders,
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


def _page_link(
    procurement_id: int,
    stages: set[ItemStage],
    group: str,
    order_id: int | None,
) -> str:
    """Адреса сторінки закупівлі зі збереженням фільтрів і режиму групування."""
    parts = [f"stage={st.value}" for st in ItemStage if st in stages]
    if group != "module":
        parts.append(f"group={group}")
    if order_id is not None:
        parts.append(f"order={order_id}")
    query = "&".join(parts)
    return f"/procurements/{procurement_id}" + (f"?{query}" if query else "")


def _export_link(
    procurement_id: int, stages: set[ItemStage], order_id: int | None, group: str
) -> str:
    """Архів документів рівно по тому, що зараз відфільтровано."""
    parts = [f"stage={st.value}" for st in ItemStage if st in stages]
    if order_id is not None:
        parts.append(f"order={order_id}")
    if group != "module":
        parts.append(f"group={group}")
    query = "&".join(parts)
    return f"/procurements/{procurement_id}/documents.zip" + (f"?{query}" if query else "")


@router.get("/procurements/{procurement_id}", response_class=HTMLResponse)
def procurement_details(
    request: Request,
    procurement_id: int,
    stage: list[str] = Query([]),
    group: str = Query("module"),
    order: int | None = Query(None),
    uow: UnitOfWork = Depends(get_uow),
) -> HTMLResponse:
    details = uow.get_procurement_details(procurement_id)
    suppliers = uow.list_suppliers()
    payers = uow.list_payers()

    stage_counts = dict.fromkeys(ItemStage, 0)
    for view in details.items:
        stage_counts[view.item.stage] += 1
    selected_stages = {ItemStage(s) for s in stage if s}
    group_mode = group if group in GROUP_MODES else "module"
    visible_items = [
        v
        for v in details.items
        if (not selected_stages or v.item.stage in selected_stages)
        and (order is None or v.item.order_id == order)
    ]
    if group_mode == "order":
        visible_items = sort_for_orders(visible_items, details.orders)
    groups = build_groups(group_mode, visible_items, details.orders)
    return templates.TemplateResponse(
        request,
        "procurement_detail.html",
        {
            "d": details,
            "visible_items": visible_items,
            "groups": groups,
            "group_mode": group_mode,
            "group_links": {
                mode: _page_link(procurement_id, selected_stages, mode, order)
                for mode in GROUP_MODES
            },
            "order_filter": order,
            # why: макроси Jinja не бачать {% set %} усередині block, тож ознака
            # «групи згорнуті за замовчуванням» приходить з контексту.
            "collapsed_default": not selected_stages,
            "order_links": {
                view.order.id: _page_link(procurement_id, selected_stages, "order", view.order.id)
                for view in details.orders
            },
            "clear_order_link": _page_link(procurement_id, selected_stages, group_mode, None),
            "export_link": _export_link(procurement_id, selected_stages, order, group_mode),
            "selected_stages": selected_stages,
            "stage_links": {
                st: _page_link(
                    procurement_id,
                    {s for s in ItemStage if (s in selected_stages) != (s is st)},
                    group_mode,
                    order,
                )
                for st in ItemStage
            },
            "all_link": _page_link(procurement_id, set(), group_mode, order),
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
def open_procurement_folder(procurement_id: int, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Reveal the procurement's document folder in the OS file manager (local run only)."""
    procurement = uow.procurements.get(procurement_id)
    uow.storage.reveal_folder(procurement.name)
    return Response(status_code=204)


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
    module: str = Form(""),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    uow.add_line_item(
        procurement_id,
        LineItemInput(
            name=name,
            specification=specification,
            qty_required=_parse_optional_float(qty_required) or 0.0,
            unit_price=_parse_optional_float(unit_price),
            module=module,
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
    module: str = Form(""),
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
            module=module,
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
    resolved_supplier_id = uow.resolve_supplier(
        int(supplier_id) if supplier_id.strip() else None,
        new_supplier_name,
        SupplierSource(new_supplier_source),
    )
    if resolved_supplier_id is None:
        raise InvalidInputError("Оберіть постачальника або введіть назву нового")
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


@router.post("/offers/{offer_id}/delete")
def delete_offer(offer_id: int, uow: UnitOfWork = Depends(get_uow)) -> RedirectResponse:
    offer = uow.offers.get(offer_id)
    procurement_id = uow.items.get(offer.line_item_id).procurement_id
    uow.delete_offer(offer_id)
    return RedirectResponse(f"/procurements/{procurement_id}", status_code=303)
