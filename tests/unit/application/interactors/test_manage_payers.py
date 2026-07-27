"""Unit tests for payer commands: free-form requisites parsing."""

from __future__ import annotations

import pytest

from procflow.application.dto import PayerInput
from procflow.application.uow import UnitOfWork
from procflow.domain.exceptions import InvalidInputError

# why: дані повністю вигадані — реальні реквізити в публічному репозиторії неприпустимі
_BLOCK = """БО «БЛАГОДІЙНИЙ ФОНД „ПРИКЛАД“»
Юр. адреса: 01001, місто Київ, вулиця Прикладна,
будинок 1,
код за ЄДРПОУ 12345678,
тел.: +380 (00) 000-00-00"""

_BLOCK_WITH_IBAN = """Тестенко Тест Тестович
IBAN
UA000000000000000000000000001
ІПН/ЄДРПОУ
0000000000"""


def test_create_from_pasted_block_extracts_name_and_edrpou(uow: UnitOfWork) -> None:
    payer = uow.create_payer(PayerInput(requisites=_BLOCK))

    assert payer.name == "БО «БЛАГОДІЙНИЙ ФОНД „ПРИКЛАД“»"
    assert payer.tax_id == "12345678"  # не телефон і не індекс
    assert payer.iban == ""
    assert payer.copy_text == _BLOCK


def test_create_from_block_with_iban(uow: UnitOfWork) -> None:
    payer = uow.create_payer(PayerInput(requisites=_BLOCK_WITH_IBAN))

    assert payer.name == "Тестенко Тест Тестович"
    assert payer.iban == "UA000000000000000000000000001"
    assert payer.tax_id == "0000000000"


def test_copy_text_composed_when_no_block(uow: UnitOfWork) -> None:
    payer = uow.create_payer(PayerInput(name="Фонд", iban="UA1", tax_id="12345678"))
    assert "Отримувач: Фонд" in payer.copy_text
    assert "IBAN: UA1" in payer.copy_text


def test_empty_input_rejected(uow: UnitOfWork) -> None:
    with pytest.raises(InvalidInputError):
        uow.create_payer(PayerInput())
