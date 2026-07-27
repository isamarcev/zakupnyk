"""Unit tests for the Excel import use-case."""

from __future__ import annotations

from procflow.application.dto import ImportedOffer, ImportedRow, ImportedSheet
from procflow.application.uow import UnitOfWork
from procflow.domain.entities import SupplierSource


def _sheet() -> ImportedSheet:
    return ImportedSheet(
        title="Потреба для віннеці",
        rows=[
            ImportedRow(
                name="Монітор 19",
                specification="Екран 19",
                qty_required=20,
                qty_ordered=0,
                qty_in_progress=0,
                unit_price=14500,
                offers=[
                    ImportedOffer(source=SupplierSource.PROM, url="https://prom.ua/x", price=14500),
                    ImportedOffer(source=SupplierSource.ROZETKA, url="", price=15000),
                    ImportedOffer(
                        source=SupplierSource.DISTRIBUTOR,
                        url="https://www.bnbfly.com.ua/ua/p245-patch",
                        price=7200,
                    ),
                ],
            )
        ],
    )


def test_import_creates_procurement_items_suppliers_offers(uow: UnitOfWork) -> None:
    created = uow.import_needs([_sheet()])

    assert len(created) == 1
    assert created[0].id is not None
    items = uow.items.list_for_procurement(created[0].id)
    assert len(items) == 1
    assert items[0].id is not None
    offers = uow.offers.list_for_item(items[0].id)
    assert len(offers) == 3
    supplier_names = {supplier.name for _, supplier in offers}
    # дистриб'ютор отримує ім'я з домену посилання, а не розмите «Дистриб'ютор»
    assert supplier_names == {"Prom.ua", "Rozetka", "bnbfly.com.ua"}


def test_import_reuses_suppliers_between_rows(uow: UnitOfWork) -> None:
    uow.import_needs([_sheet()])
    uow.import_needs([_sheet()])

    assert len(uow.suppliers.list_all()) == 3  # not duplicated
