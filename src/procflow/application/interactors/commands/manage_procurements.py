"""Commands for the procurement aggregate: project itself and its line items."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from procflow.application.dto import (
    CreateProcurementInput,
    LineItemInput,
    UpdateProcurementInput,
)
from procflow.application.interfaces.repositories import (
    LineItemRepository,
    ProcurementRepository,
)
from procflow.domain.entities import ItemStage, LineItem, Procurement, ProcurementStatus
from procflow.domain.exceptions import InvalidInputError


def _require_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise InvalidInputError("Назва не може бути порожньою")
    return cleaned


@dataclass(slots=True)
class CreateProcurement:
    procurements: ProcurementRepository

    def __call__(self, cmd: CreateProcurementInput) -> Procurement:
        now = datetime.now()
        return self.procurements.add(
            Procurement(
                id=None,
                name=_require_name(cmd.name),
                description=cmd.description.strip(),
                status=ProcurementStatus.DRAFT,
                created_at=now,
                updated_at=now,
            )
        )


@dataclass(slots=True)
class UpdateProcurement:
    procurements: ProcurementRepository

    def __call__(self, cmd: UpdateProcurementInput) -> Procurement:
        procurement = self.procurements.get(cmd.procurement_id)
        procurement.name = _require_name(cmd.name)
        procurement.description = cmd.description.strip()
        procurement.status = cmd.status
        procurement.updated_at = datetime.now()
        self.procurements.update(procurement)
        return procurement


@dataclass(slots=True)
class DeleteProcurement:
    procurements: ProcurementRepository

    def __call__(self, procurement_id: int) -> None:
        self.procurements.get(procurement_id)  # raises if missing
        self.procurements.delete(procurement_id)


@dataclass(slots=True)
class AddLineItem:
    procurements: ProcurementRepository
    items: LineItemRepository

    def __call__(self, procurement_id: int, data: LineItemInput) -> LineItem:
        self.procurements.get(procurement_id)  # raises if missing
        return self.items.add(
            LineItem(
                id=None,
                procurement_id=procurement_id,
                name=_require_name(data.name),
                specification=data.specification.strip(),
                qty_required=data.qty_required,
                qty_ordered=data.qty_ordered,
                qty_in_progress=data.qty_in_progress,
                unit_price=data.unit_price,
            )
        )


@dataclass(slots=True)
class UpdateLineItem:
    items: LineItemRepository

    def __call__(self, item_id: int, data: LineItemInput) -> LineItem:
        item = self.items.get(item_id)
        item.name = _require_name(data.name)
        item.specification = data.specification.strip()
        item.qty_required = data.qty_required
        item.qty_ordered = data.qty_ordered
        item.qty_in_progress = data.qty_in_progress
        item.unit_price = data.unit_price
        self.items.update(item)
        return item


@dataclass(slots=True)
class SetItemStage:
    """Quick stage switch from the items table (no full edit form)."""

    items: LineItemRepository

    def __call__(self, item_id: int, stage: ItemStage) -> LineItem:
        item = self.items.get(item_id)
        item.stage = stage
        self.items.update(item)
        return item


@dataclass(slots=True)
class DeleteLineItem:
    items: LineItemRepository

    def __call__(self, item_id: int) -> None:
        self.items.get(item_id)  # raises if missing
        self.items.delete(item_id)
