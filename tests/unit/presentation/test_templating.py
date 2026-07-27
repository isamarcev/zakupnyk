"""Unit tests for Jinja template filters."""

from __future__ import annotations

from procflow.presentation.templating import _money


def test_money_keeps_fractional_part() -> None:
    assert _money(1327.5) == "1 327,5"


def test_money_whole_value_has_no_decimals() -> None:
    assert _money(2655.0) == "2 655"


def test_money_two_decimal_places() -> None:
    assert _money(1234567.89) == "1 234 567,89"


def test_money_none_is_dash() -> None:
    assert _money(None) == "—"
