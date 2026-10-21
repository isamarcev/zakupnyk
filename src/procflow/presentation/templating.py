"""Jinja2 environment with project filters."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from fastapi.templating import Jinja2Templates

from procflow.application.formatting import money, qty

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _date_uk(value: datetime | date | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%d.%m.%Y")


def make_templates() -> Jinja2Templates:
    """Build the templates object used by all routers."""
    templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))
    templates.env.filters["money"] = money
    templates.env.filters["qty"] = qty
    templates.env.filters["date_uk"] = _date_uk
    return templates


templates = make_templates()
