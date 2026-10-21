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
    StageChangeRepository,
)
from procflow.domain.entities import (
    ItemStage,
    LineItem,
    Procurement,
    ProcurementStatus,
    StageChange,
)
from procflow.domain.exceptions import InvalidInputError


def _require_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise InvalidInputError("Назва не може бути порожньою")
    return cleaned


def _clean_module(module: str | None) -> str | None:
    """Empty/whitespace module means «без модуля» (a flat, ungrouped item)."""
    if module is None:
        return None
    cleaned = module.strip()
    return cleaned or None


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
                module=_clean_module(data.module),
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
        item.module = _clean_module(data.module)
        self.items.update(item)
        return item


@dataclass(slots=True)
class SetItemStage:
    """Quick stage switch from the items table (no full edit form)."""

    items: LineItemRepository
    stage_changes: StageChangeRepository

    def __call__(self, item_id: int, stage: ItemStage) -> LineItem:
        item = self.items.get(item_id)
        if item.stage is stage:
            return item  # why: повтор тієї ж стадії не має засмічувати історію
        item.stage = stage
        self.items.update(item)
        assert item.id is not None
        self.stage_changes.add(
            StageChange(id=None, line_item_id=item.id, stage=stage, changed_at=datetime.now())
        )
        return item


@dataclass(slots=True)
class DeleteLineItem:
    items: LineItemRepository

    def __call__(self, item_id: int) -> None:
        self.items.get(item_id)  # raises if missing
        self.items.delete(item_id)
