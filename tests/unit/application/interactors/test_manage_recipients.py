"""Unit tests for recipient commands: free-form block parsing."""

from __future__ import annotations

import pytest

from procflow.application.dto import RecipientInput
from procflow.application.uow import UnitOfWork
from procflow.domain.exceptions import InvalidInputError

# why: дані повністю вигадані — реальні контакти в публічному репозиторії неприпустимі
_BLOCK = """Отримувач
Тестенко Тарас
Телефон отримувача
+380 00 111 22 33
Адреса
смт. Вигадане (Тестова обл., Умовний р-н.), №1: вул. Прикладна, 1"""


def test_create_from_block_extracts_name_and_phone(uow: UnitOfWork) -> None:
    recipient = uow.create_recipient(RecipientInput(block=_BLOCK, purpose="Для доставки"))

    # ім'я — перший справжній рядок (мітку "Отримувач" і телефон пропускаємо)
    assert recipient.name == "Тестенко Тарас"
    assert recipient.phone == "+380 00 111 22 33"
    assert recipient.purpose == "Для доставки"
    assert recipient.copy_text == _BLOCK


def test_copy_text_composed_when_no_block(uow: UnitOfWork) -> None:
    recipient = uow.create_recipient(
        RecipientInput(name="Іван", phone="0991112233", address="Київ, відділення 1")
    )
    assert "Отримувач: Іван" in recipient.copy_text
    assert "Телефон отримувача: 0991112233" in recipient.copy_text
    assert "Адреса: Київ, відділення 1" in recipient.copy_text


def test_empty_input_rejected(uow: UnitOfWork) -> None:
    with pytest.raises(InvalidInputError):
        uow.create_recipient(RecipientInput())


def test_search_by_phone(uow: UnitOfWork) -> None:
    uow.create_recipient(RecipientInput(block=_BLOCK))
    found = uow.list_recipients(query="111 22")
    assert len(found) == 1


def test_phones_lists_every_number_in_block(uow: UnitOfWork) -> None:
    block = _BLOCK + "\n\nДля документів:\nКиїв, НП 12345, Прикладенко Петро, +380 00 444 55 66"
    recipient = uow.create_recipient(RecipientInput(block=block))

    # обидва номери стають окремими кнопками; короткий «12345» не вважається телефоном
    assert recipient.phones == ["+380 00 111 22 33", "+380 00 444 55 66"]
