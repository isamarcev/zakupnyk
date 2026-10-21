"""Routes for supplier orders: group positions bought by one invoice."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse

from procflow.application.dto import SupplierOrderInput
from procflow.application.uow import UnitOfWork
from procflow.domain.entities import ItemStage, SupplierSource
from procflow.domain.exceptions import InvalidInputError
from procflow.presentation.api.deps import get_uow

router = APIRouter()


def _order_input(
    title: str, supplier_id: str, new_supplier_name: str, new_supplier_source: str, note: str
) -> SupplierOrderInput:
    return SupplierOrderInput(
        title=title,
        supplier_id=int(supplier_id) if supplier_id.strip() else None,
        new_supplier_name=new_supplier_name,
        new_supplier_source=SupplierSource(new_supplier_source),
        note=note,
    )


def _require_items(item_ids: list[int]) -> list[int]:
    if not item_ids:
        raise InvalidInputError("Спочатку виберіть позиції галочками")
    return item_ids


@router.post("/procurements/{procurement_id}/orders")
def create_order(
    procurement_id: int,
    title: str = Form(""),
    supplier_id: str = Form(""),
    new_supplier_name: str = Form(""),
    new_supplier_source: str = Form(SupplierSource.DISTRIBUTOR.value),
    note: str = Form(""),
    item_ids: list[int] = Form([]),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    """Створити замовлення — зазвичай одразу з вибраних галочками позицій."""
    uow.create_order(
        procurement_id,
        _order_input(title, supplier_id, new_supplier_name, new_supplier_source, note),
        item_ids,
    )
    return RedirectResponse(f"/procurements/{procurement_id}", status_code=303)


@router.post("/orders/assign")
def assign_items(
    order_id: str = Form(""),
    item_ids: list[int] = Form([]),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    """Додати вибрані позиції до наявного замовлення."""
    if not order_id.strip():
        raise InvalidInputError("Оберіть замовлення зі списку")
    order = uow.assign_items_to_order(int(order_id), _require_items(item_ids))
    return RedirectResponse(f"/procurements/{order.procurement_id}", status_code=303)


@router.post("/orders/detach")
def detach_items(
    item_ids: list[int] = Form([]),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    """Вийняти позиції з їхніх замовлень (позиція знову купується окремо)."""
    procurement_id = uow.items.get(_require_items(item_ids)[0]).procurement_id
    uow.detach_items_from_order(item_ids)
    return RedirectResponse(f"/procurements/{procurement_id}", status_code=303)


@router.post("/items/bulk-stage")
def bulk_stage(
    stage: str = Form(...),
    item_ids: list[int] = Form([]),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    """Одна стадія на всі вибрані позиції (історія пишеться по кожній)."""
    procurement_id = uow.items.get(_require_items(item_ids)[0]).procurement_id
    uow.set_items_stage(item_ids, ItemStage(stage))
    return RedirectResponse(f"/procurements/{procurement_id}", status_code=303)


@router.post("/orders/{order_id}/stage")
def set_order_stage(
    order_id: int,
    stage: str = Form(...),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    order = uow.set_order_stage(order_id, ItemStage(stage))
    return RedirectResponse(f"/procurements/{order.procurement_id}", status_code=303)


@router.post("/orders/{order_id}/update")
def update_order(
    order_id: int,
    title: str = Form(""),
    supplier_id: str = Form(""),
    new_supplier_name: str = Form(""),
    new_supplier_source: str = Form(SupplierSource.DISTRIBUTOR.value),
    note: str = Form(""),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    order = uow.update_order(
        order_id, _order_input(title, supplier_id, new_supplier_name, new_supplier_source, note)
    )
    return RedirectResponse(f"/procurements/{order.procurement_id}", status_code=303)


@router.post("/orders/{order_id}/items")
def add_items_to_order(
    order_id: int,
    item_ids: list[int] = Form([]),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    order = uow.assign_items_to_order(order_id, _require_items(item_ids))
    return RedirectResponse(f"/procurements/{order.procurement_id}", status_code=303)


@router.post("/orders/{order_id}/delete")
def delete_order(order_id: int, uow: UnitOfWork = Depends(get_uow)) -> RedirectResponse:
    """Видалити групу; позиції та документи лишаються, лише відвʼязуються."""
    procurement_id = uow.delete_order(order_id)
    return RedirectResponse(f"/procurements/{procurement_id}", status_code=303)
