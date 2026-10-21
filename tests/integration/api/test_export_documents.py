"""Експорт документів одним архівом: плоский список файлів + перелік назв."""

from __future__ import annotations

import io
import zipfile

import httpx
from fastapi.testclient import TestClient


def _setup(client: TestClient) -> int:
    """Дві позиції в замовленні (спільний рахунок), третя окремо + накладна."""
    created = client.post("/procurements", data={"name": "Експорт"}, follow_redirects=False)
    procurement_id = int(created.headers["location"].rsplit("/", 1)[-1])
    for name, module in (("Кнопка", "Комутація"), ("Запобіжник", "Комутація"), ("Реле", "Привід")):
        client.post(
            f"/procurements/{procurement_id}/items",
            data={"name": name, "qty_required": "2", "unit_price": "50", "module": module},
            follow_redirects=False,
        )
    client.post(
        f"/procurements/{procurement_id}/orders",
        data={"title": "Рахунок 14802", "new_supplier_name": "relcoma.com.ua", "item_ids": [1, 2]},
        follow_redirects=False,
    )
    client.post(
        "/orders/1/documents",
        data={"title": "Рахунок 14802", "kind": "invoice"},
        files={"file": ("14802.pdf", b"%PDF-1.4 order", "application/pdf")},
        follow_redirects=False,
    )
    client.post(
        "/items/3/documents",
        data={"title": "Рахунок окремий", "kind": "invoice"},
        files={"file": ("solo.pdf", b"%PDF-1.4 solo", "application/pdf")},
        follow_redirects=False,
    )
    client.post(
        "/items/3/documents",
        data={"title": "Накладна", "kind": "waybill"},
        files={"file": ("ttn.pdf", b"%PDF-1.4 ttn", "application/pdf")},
        follow_redirects=False,
    )
    return procurement_id


def _archive(response: httpx.Response) -> zipfile.ZipFile:
    return zipfile.ZipFile(io.BytesIO(response.content))


def test_archive_is_a_flat_list_of_files(client: TestClient) -> None:
    procurement_id = _setup(client)

    response = client.get(f"/procurements/{procurement_id}/documents.zip")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    archive = _archive(response)
    assert sorted(archive.namelist()) == ["14802.pdf", "_перелік.txt", "solo.pdf", "ttn.pdf"]
    assert archive.read("14802.pdf") == b"%PDF-1.4 order"


def test_listing_is_a_specification_grouped_by_modules(client: TestClient) -> None:
    procurement_id = _setup(client)

    archive = _archive(client.get(f"/procurements/{procurement_id}/documents.zip"))
    assert archive.read("_перелік.txt").decode() == (
        "Група 1\n"
        "Кнопка — 2 шт, ціна 50, сума 100 грн\n"
        "Запобіжник — 2 шт, ціна 50, сума 100 грн\n"
        "Підсумок «Група 1»: 200 грн (2 поз.)\n"
        "\n"
        "Група 2\n"
        "Реле — 2 шт, ціна 50, сума 100 грн\n"
        "Підсумок «Група 2»: 100 грн (1 поз.)\n"
        "\n"
        "Разом: 300 грн\n"
    )


def test_listing_follows_the_order_grouping(client: TestClient) -> None:
    """У режимі замовлень групи ті самі, що на сторінці, але без назв рахунків."""
    procurement_id = _setup(client)

    archive = _archive(client.get(f"/procurements/{procurement_id}/documents.zip?group=order"))
    listing = archive.read("_перелік.txt").decode()
    assert listing.startswith("Група 1\nКнопка")
    assert "Запобіжник" in listing.split("Підсумок «Група 1»")[0]
    assert "Рахунок 14802" not in listing and "relcoma" not in listing
    assert listing.endswith("Разом: 300 грн\n")


def test_listing_without_groups_is_a_plain_list(client: TestClient) -> None:
    procurement_id = _setup(client)

    archive = _archive(client.get(f"/procurements/{procurement_id}/documents.zip?group=flat"))
    listing = archive.read("_перелік.txt").decode()
    assert "Група" not in listing
    assert listing.splitlines()[0] == "Кнопка — 2 шт, ціна 50, сума 100 грн"
    assert listing.splitlines()[-2:] == ["", "Разом: 300 грн"]


def test_kind_filter_exports_invoices_only(client: TestClient) -> None:
    procurement_id = _setup(client)

    response = client.get(f"/procurements/{procurement_id}/documents.zip?kind=invoice")
    assert sorted(_archive(response).namelist()) == ["14802.pdf", "_перелік.txt", "solo.pdf"]
    # імʼя архіву каже, що всередині: «… — рахунки.zip»
    from urllib.parse import unquote

    assert unquote(response.headers["content-disposition"]).endswith("— рахунки.zip")


def test_archive_follows_the_order_filter(client: TestClient) -> None:
    procurement_id = _setup(client)

    names = _archive(client.get(f"/procurements/{procurement_id}/documents.zip?order=1")).namelist()
    assert sorted(names) == ["14802.pdf", "_перелік.txt"]


def test_archive_follows_the_stage_filter(client: TestClient) -> None:
    procurement_id = _setup(client)
    client.post("/items/3/stage", data={"stage": "paid"}, follow_redirects=False)

    names = _archive(
        client.get(f"/procurements/{procurement_id}/documents.zip?stage=paid&kind=invoice")
    ).namelist()
    assert sorted(names) == ["_перелік.txt", "solo.pdf"]


def test_archive_of_selected_items_only(client: TestClient) -> None:
    procurement_id = _setup(client)

    names = _archive(client.get(f"/procurements/{procurement_id}/documents.zip?item=3")).namelist()
    assert sorted(names) == ["_перелік.txt", "solo.pdf", "ttn.pdf"]


def test_same_file_names_do_not_collide(client: TestClient) -> None:
    procurement_id = _setup(client)
    client.post(
        "/orders/1/documents",
        data={"title": "Квитанція", "kind": "invoice"},
        files={"file": ("14802.pdf", b"%PDF-1.4 receipt", "application/pdf")},
        follow_redirects=False,
    )

    archive = _archive(client.get(f"/procurements/{procurement_id}/documents.zip?order=1"))
    assert sorted(archive.namelist()) == ["14802 (2).pdf", "14802.pdf", "_перелік.txt"]
    assert archive.read("14802 (2).pdf") == b"%PDF-1.4 receipt"


def test_missing_file_does_not_break_the_archive(client: TestClient, container: object) -> None:
    procurement_id = _setup(client)
    files_dir = container.settings.files_dir  # type: ignore[attr-defined]
    for path in files_dir.rglob("14802*"):
        path.unlink()

    names = _archive(client.get(f"/procurements/{procurement_id}/documents.zip")).namelist()
    assert "14802.pdf.ВІДСУТНІЙ.txt" in names
    assert "solo.pdf" in names
