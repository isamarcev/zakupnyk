"""Supplier and offer entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SupplierSource(str, Enum):
    """Where the supplier was found / what marketplace they sell on."""

    PROM = "prom"
    ROZETKA = "rozetka"
    DISTRIBUTOR = "distributor"
    OTHER = "other"

    @property
    def label_uk(self) -> str:
        """Ukrainian display label."""
        return {
            SupplierSource.PROM: "Prom.ua",
            SupplierSource.ROZETKA: "Rozetka",
            SupplierSource.DISTRIBUTOR: "Дистриб'ютор",
            SupplierSource.OTHER: "Інше",
        }[self]


@dataclass(slots=True)
class Supplier:
    """A vendor we buy from (marketplace seller, distributor, shop)."""

    id: int | None
    name: str
    source: SupplierSource
    contacts: str = ""
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)


def normalize_url(raw: str) -> str:
    """'radio-shop.com.ua/p1' → 'https://radio-shop.com.ua/p1'; keeps an existing scheme.

    Без схеми браузер трактує href як відносний шлях і веде на /procurements/….
    """
    url = raw.strip()
    if url and "://" not in url:
        return f"https://{url}"
    return url


@dataclass(slots=True)
class Offer:
    """A price quote: line item available at a supplier for a given price."""

    id: int | None
    line_item_id: int
    supplier_id: int
    url: str = ""
    price: float | None = None
    note: str = ""
    created_at: datetime = field(default_factory=datetime.now)
