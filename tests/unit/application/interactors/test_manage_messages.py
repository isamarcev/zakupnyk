"""Unit tests for the line-item message thread."""

from __future__ import annotations

import pytest

from procflow.application.dto import CreateProcurementInput, LineItemInput
from procflow.application.uow import UnitOfWork
from procflow.domain.exceptions import InvalidInputError


def _item(uow: UnitOfWork) -> int:
    procurement = uow.create_procurement(CreateProcurementInput(name="П"))
    assert procurement.id is not None
    item = uow.add_line_item(procurement.id, LineItemInput(name="Антена", qty_required=1))
    assert item.id is not None
    return item.id


def test_add_message_and_latest(uow: UnitOfWork) -> None:
    item_id = _item(uow)
    uow.add_message(item_id, "перше")
    uow.add_message(item_id, "друге")

    details = uow.get_line_item_details(item_id)
    assert [m.text for m in details.messages] == ["друге", "перше"]  # newest first
    assert uow.messages.latest_for_item(item_id).text == "друге"


def test_empty_message_rejected(uow: UnitOfWork) -> None:
    item_id = _item(uow)
    with pytest.raises(InvalidInputError):
        uow.add_message(item_id, "   ")


def test_last_message_shown_in_procurement_view(uow: UnitOfWork) -> None:
    item_id = _item(uow)
    uow.add_message(item_id, "очікую рахунок")
    procurement_id = uow.items.get(item_id).procurement_id

    details = uow.get_procurement_details(procurement_id)
    assert details.items[0].last_message is not None
    assert details.items[0].last_message.text == "очікую рахунок"
