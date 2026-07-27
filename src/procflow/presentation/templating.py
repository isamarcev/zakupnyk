"""Jinja2 environment with project filters."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from fastapi.templating import Jinja2Templates

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _money(value: float | None) -> str:
    """Format 1234567.5 → '1 234 567,5'; whole values without decimals."""
    if value is None:
        return "—"
    whole, _, frac = f"{value:,.2f}".partition(".")
    frac = frac.rstrip("0")
    grouped = whole.replace(",", " ")
    return f"{grouped},{frac}" if frac else grouped


def _qty(value: float) -> str:
    """Format quantity without trailing .0."""
    return f"{value:g}"


def _date_uk(value: datetime | date | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%d.%m.%Y")


def make_templates() -> Jinja2Templates:
    """Build the templates object used by all routers."""
    templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))
    templates.env.filters["money"] = _money
    templates.env.filters["qty"] = _qty
    templates.env.filters["date_uk"] = _date_uk
    return templates


templates = make_templates()
