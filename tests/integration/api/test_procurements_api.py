"""Integration tests for procurement routes (success + failure)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_and_view_procurement(client: TestClient) -> None:
    response = client.post(
        "/procurements",
        data={"name": "Тестова закупівля", "description": "опис"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    detail_url = response.headers["location"]

    page = client.get(detail_url)
    assert page.status_code == 200
    assert "Тестова закупівля" in page.text


def test_missing_procurement_returns_404_page(client: TestClient) -> None:
    response = client.get("/procurements/424242")
    assert response.status_code == 404
    assert "не знайдено" in response.text


def test_upload_and_download_document(client: TestClient) -> None:
    created = client.post(
        "/procurements", data={"name": "Закупівля з документом"}, follow_redirects=False
    )
    procurement_id = created.headers["location"].rsplit("/", 1)[-1]
    client.post(
        f"/procurements/{procurement_id}/items",
        data={"name": "Антена патч", "qty_required": "2"},
        follow_redirects=False,
    )

    # основний сценарій: документ вантажиться до конкретної позиції
    upload = client.post(
        "/items/1/documents",
        data={"title": "Рахунок №1", "kind": "invoice", "amount": "1234.5"},
        files={"file": ("invoice.pdf", b"%PDF-1.4 test", "application/pdf")},
        follow_redirects=False,
    )
    assert upload.status_code == 303

    page = client.get(f"/procurements/{procurement_id}")
    assert "Рахунок №1" in page.text
    # документ показано біля позиції (колонка «Документи» рядка)
    assert "📄 Рахунок №1" in page.text

    # the file link is present and downloadable
    file_id = page.text.split("/documents/")[1].split("/file")[0]
    downloaded = client.get(f"/documents/{file_id}/file")
    assert downloaded.status_code == 200
    assert downloaded.content.startswith(b"%PDF")

    # документ, прикріплений до позиції, можна видалити
    deleted = client.post(f"/documents/{file_id}/delete", follow_redirects=False)
    assert deleted.status_code == 303
    page = client.get(f"/procurements/{procurement_id}")
    assert "Рахунок №1" not in page.text


def test_stage_switch_and_filter(client: TestClient) -> None:
    created = client.post("/procurements", data={"name": "Зі стадіями"}, follow_redirects=False)
    procurement_id = created.headers["location"].rsplit("/", 1)[-1]
    client.post(
        f"/procurements/{procurement_id}/items",
        data={"name": "Антена", "qty_required": "1"},
        follow_redirects=False,
    )

    switch = client.post(
        "/items/1/stage", data={"stage": "awaiting_invoice"}, follow_redirects=False
    )
    assert switch.status_code == 303

    filtered = client.get(f"/procurements/{procurement_id}?stage=awaiting_invoice")
    assert "Антена" in filtered.text
    empty = client.get(f"/procurements/{procurement_id}?stage=paid")
    assert "Антена" not in empty.text.split("Додати позицію")[0]


def test_multi_stage_filter_and_spec_block(client: TestClient) -> None:
    created = client.post("/procurements", data={"name": "Мультистадії"}, follow_redirects=False)
    procurement_id = created.headers["location"].rsplit("/", 1)[-1]
    for name in ("Антена", "Кабель", "Перехідник"):
        client.post(
            f"/procurements/{procurement_id}/items",
            data={"name": name, "qty_required": "2", "unit_price": "1327.5"},
            follow_redirects=False,
        )
    client.post("/items/1/stage", data={"stage": "awaiting_invoice"}, follow_redirects=False)
    client.post("/items/2/stage", data={"stage": "paid"}, follow_redirects=False)

    page = client.get(f"/procurements/{procurement_id}?stage=awaiting_invoice&stage=paid")
    listing = page.text.split("Додати позицію")[0]
    assert "Антена" in listing
    assert "Кабель" in listing
    assert "Перехідник" not in listing
    # блок специфікації з кнопкою копіювання та незаокругленою ціною
    assert "Копіювати специфікацію" in listing
    assert "1 327,5" in listing
    # разом по видимих позиціях: 2 × 1327.5 × 2 позиції = 5310
    assert "Разом: 5 310 грн" in listing


def test_offer_url_without_scheme_becomes_absolute(client: TestClient) -> None:
    created = client.post("/procurements", data={"name": "З пропозицією"}, follow_redirects=False)
    procurement_id = created.headers["location"].rsplit("/", 1)[-1]
    client.post(
        f"/procurements/{procurement_id}/items",
        data={"name": "Антена", "qty_required": "1"},
        follow_redirects=False,
    )
    client.post(
        "/items/1/offers",
        data={
            "new_supplier_name": "radio-shop.com.ua",
            "new_supplier_source": "distributor",
            "url": "radio-shop.com.ua/p123",
            "price": "100",
        },
        follow_redirects=False,
    )

    page = client.get(f"/procurements/{procurement_id}")
    # без схеми браузер трактував би href як відносний і вів на /procurements/…
    assert 'href="https://radio-shop.com.ua/p123"' in page.text


def test_line_items_grouped_by_module(client: TestClient) -> None:
    created = client.post("/procurements", data={"name": "Модульна"}, follow_redirects=False)
    procurement_id = created.headers["location"].rsplit("/", 1)[-1]
    client.post(
        f"/procurements/{procurement_id}/items",
        data={"name": "Мотор dc", "qty_required": "2", "module": "Модуль поворотний"},
        follow_redirects=False,
    )
    client.post(
        f"/procurements/{procurement_id}/items",
        data={"name": "Розьем xt60", "qty_required": "1", "module": "Модуль комутаційний"},
        follow_redirects=False,
    )

    listing = client.get(f"/procurements/{procurement_id}").text.split("Додати позицію")[0]
    assert "🧩 Модуль поворотний" in listing
    assert "🧩 Модуль комутаційний" in listing


def test_module_groups_collapsed_by_default(client: TestClient) -> None:
    created = client.post("/procurements", data={"name": "Згортання"}, follow_redirects=False)
    procurement_id = created.headers["location"].rsplit("/", 1)[-1]
    client.post(
        f"/procurements/{procurement_id}/items",
        data={"name": "Мотор dc", "qty_required": "2", "module": "Модуль поворотний"},
        follow_redirects=False,
    )

    page = client.get(f"/procurements/{procurement_id}").text
    # заголовок модуля клікабельний (data-mod-toggle) і позиція згорнута за замовчуванням
    assert "data-mod-toggle=" in page
    assert "mod-item is-collapsed" in page
    assert "Розгорнути всі модулі" in page


def test_stage_filter_expands_module_groups(client: TestClient) -> None:
    created = client.post("/procurements", data={"name": "Фільтр+групи"}, follow_redirects=False)
    procurement_id = created.headers["location"].rsplit("/", 1)[-1]
    client.post(
        f"/procurements/{procurement_id}/items",
        data={"name": "Мотор dc", "qty_required": "1", "module": "Модуль поворотний"},
        follow_redirects=False,
    )
    client.post("/items/1/stage", data={"stage": "paid"}, follow_redirects=False)

    listing = client.get(f"/procurements/{procurement_id}?stage=paid").text.split("Додати позицію")[
        0
    ]
    # при активному фільтрі групи показані розгорнутими (рядок без is-collapsed)
    assert "mod-item is-collapsed" not in listing
    assert "Мотор dc" in listing


def test_flat_procurement_shows_no_module_headers(client: TestClient) -> None:
    created = client.post("/procurements", data={"name": "Плоска"}, follow_redirects=False)
    procurement_id = created.headers["location"].rsplit("/", 1)[-1]
    client.post(
        f"/procurements/{procurement_id}/items",
        data={"name": "Кабель", "qty_required": "1"},
        follow_redirects=False,
    )

    listing = client.get(f"/procurements/{procurement_id}").text.split("Додати позицію")[0]
    assert "🧩" not in listing


def test_payers_crud(client: TestClient) -> None:
    response = client.post(
        "/payers",
        data={
            "name": "Тестенко Тест Тестович",
            "iban": "UA000000000000000000000000001",
            "tax_id": "0000000000",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    page = client.get("/payers")
    assert "UA000000000000000000000000001" in page.text
