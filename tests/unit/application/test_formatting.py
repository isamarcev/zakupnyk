"""Формат чисел, спільний для шаблонів і текстових експортів."""

from __future__ import annotations

from procflow.application.formatting import money, qty


def test_money_keeps_fractional_part() -> None:
    assert money(1327.5) == "1 327,5"


def test_money_whole_value_has_no_decimals() -> None:
    assert money(2655.0) == "2 655"


def test_money_two_decimal_places() -> None:
    assert money(1234567.89) == "1 234 567,89"


def test_money_none_is_dash() -> None:
    assert money(None) == "—"


def test_qty_drops_trailing_zeros() -> None:
    assert qty(6.0) == "6"
    assert qty(2.5) == "2.5"
