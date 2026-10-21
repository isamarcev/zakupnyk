"""Unit tests for procurement commands (run on real SQLite via repositories)."""

from __future__ import annotations

import pytest

from procflow.application.dto import CreateProcurementInput, LineItemInput
from procflow.application.uow import UnitOfWork
from procflow.domain.entities import ItemStage, ProcurementStatus
from procflow.domain.exceptions import InvalidInputError, ProcurementNotFoundError


def test_create_procurement_persists_with_draft_status(uow: UnitOfWork) -> None:
    procurement = uow.create_procurement(CreateProcurementInput(name="Партія 1", description="x"))

    assert procurement.id is not None
    stored = uow.procurements.get(procurement.id)
    assert stored.name == "Партія 1"
    assert stored.status is ProcurementStatus.DRAFT


def test_create_procurement_rejects_empty_name(uow: UnitOfWork) -> None:
    with pytest.raises(InvalidInputError):
        uow.create_procurement(CreateProcurementInput(name="   "))


def test_add_line_item_and_completion_flag(uow: UnitOfWork) -> None:
    procurement = uow.create_procurement(CreateProcurementInput(name="Партія 2"))
    assert procurement.id is not None

    item = uow.add_line_item(
        procurement.id, LineItemInput(name="Антена", qty_required=4, unit_price=7200)
    )
    assert item.id is not None
    assert item.total_price == 28800
    assert not item.is_complete

    item_input = LineItemInput(name="Антена", qty_required=4, qty_ordered=4, unit_price=7200)
    updated = uow.update_line_item(item.id, item_input)
    assert updated.is_complete


def test_set_item_stage_persists(uow: UnitOfWork) -> None:
    procurement = uow.create_procurement(CreateProcurementInput(name="Партія 3"))
    assert procurement.id is not None
    item = uow.add_line_item(procurement.id, LineItemInput(name="Щогла", qty_required=1))
    assert item.id is not None
    assert item.stage is ItemStage.NEW

    uow.set_item_stage(item.id, ItemStage.SENT_FOR_PAYMENT)

    assert uow.items.get(item.id).stage is ItemStage.SENT_FOR_PAYMENT


def test_line_item_module_is_trimmed_and_emptied_to_none(uow: UnitOfWork) -> None:
    procurement = uow.create_procurement(CreateProcurementInput(name="З модулями"))
    assert procurement.id is not None

    item = uow.add_line_item(
        procurement.id,
        LineItemInput(name="Мотор dc", qty_required=2, module="  Модуль поворотний  "),
    )
    assert item.id is not None
    assert item.module == "Модуль поворотний"
    assert uow.items.get(item.id).module == "Модуль поворотний"

    cleared = uow.update_line_item(
        item.id, LineItemInput(name="Мотор dc", qty_required=2, module="   ")
    )
    assert cleared.module is None
    assert uow.items.get(item.id).module is None


def test_delete_procurement_missing_raises(uow: UnitOfWork) -> None:
    with pytest.raises(ProcurementNotFoundError):
        uow.delete_procurement(99999)


def test_stage_changes_are_recorded_with_dates(uow: UnitOfWork) -> None:
    procurement = uow.create_procurement(CreateProcurementInput(name="Історія стадій"))
    assert procurement.id is not None
    item = uow.add_line_item(procurement.id, LineItemInput(name="Кабель", qty_required=1))
    assert item.id is not None

    # поки переходів не було — «з» рахуємо від дати створення позиції
    view = next(
        v for v in uow.get_procurement_details(procurement.id).items if v.item.id == item.id
    )
    assert view.stage_since == item.created_at

    uow.set_item_stage(item.id, ItemStage.AWAITING_INVOICE)
    uow.set_item_stage(item.id, ItemStage.AWAITING_INVOICE)  # повтор не пишемо в історію
    uow.set_item_stage(item.id, ItemStage.PAID)

    history = uow.stage_changes.list_for_item(item.id)
    assert [c.stage for c in history] == [ItemStage.AWAITING_INVOICE, ItemStage.PAID]

    view = next(
        v for v in uow.get_procurement_details(procurement.id).items if v.item.id == item.id
    )
    assert view.stage_since == history[-1].changed_at

    timeline = uow.get_line_item_details(item.id).stage_timeline
    assert [s.stage for s in timeline] == [
        ItemStage.NEW,
        ItemStage.AWAITING_INVOICE,
        ItemStage.PAID,
    ]
    assert timeline[0].at == item.created_at
    assert all(step.at is not None for step in timeline)
