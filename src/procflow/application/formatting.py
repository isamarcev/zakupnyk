"""Number formatting shared by templates and text exports."""

from __future__ import annotations


def money(value: float | None) -> str:
    """Format 1234567.5 → '1 234 567,5'; whole values without decimals."""
    if value is None:
        return "—"
    whole, _, frac = f"{value:,.2f}".partition(".")
    frac = frac.rstrip("0")
    grouped = whole.replace(",", " ")
    return f"{grouped},{frac}" if frac else grouped


def qty(value: float) -> str:
    """Format quantity without trailing .0."""
    return f"{value:g}"
