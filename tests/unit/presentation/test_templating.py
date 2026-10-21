"""Unit tests for Jinja template filters."""

from __future__ import annotations

from datetime import date

from procflow.presentation.templating import templates


def test_money_filter_is_wired() -> None:
    assert templates.env.filters["money"](1327.5) == "1 327,5"
    assert templates.env.filters["money"](None) == "—"


def test_qty_filter_is_wired() -> None:
    assert templates.env.filters["qty"](6.0) == "6"


def test_date_uk_filter() -> None:
    assert templates.env.filters["date_uk"](date(2026, 8, 27)) == "27.08.2026"
    assert templates.env.filters["date_uk"](None) == "—"
