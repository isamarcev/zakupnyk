"""Замовлення: групування позицій, які купуються одним рахунком в одного продавця."""

from __future__ import annotations

from fastapi.testclient import TestClient

from procflow.application.uow import UnitOfWork


def _procurement_with_items(client: TestClient, names: list[str]) -> tuple[int, list[int]]:
    created = client.post("/procurements", data={"name": "Тест замовлень"}, follow_redirects=False)
    procurement_id = int(created.headers["location"].rsplit("/", 1)[-1])
    item_ids = []
    for index, name in enumerate(names):
        client.post(
            f"/procurements/{procurement_id}/items",
            data={
                "name": name,
                "qty_required": "2",
                "unit_price": "100",
                "module": f"Модуль {index % 2 + 1}",
            },
            follow_redirects=False,
        )
        item_ids.append(index + 1)
    return procurement_id, item_ids


def test_create_order_from_selected_items(client: TestClient, uow: UnitOfWork) -> None:
    procurement_id, item_ids = _procurement_with_items(client, ["Кнопка", "Запобіжник", "Реле"])

    response = client.post(
        f"/procurements/{procurement_id}/orders",
        data={
            "title": "Рахунок 14802",
            "new_supplier_name": "relcoma.com.ua",
            "item_ids": item_ids[:2],
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    details = uow.get_procurement_details(procurement_id)
    assert len(details.orders) == 1
    order_view = details.orders[0]
    assert [v.item.name for v in order_view.items] == ["Кнопка", "Запобіжник"]
    assert order_view.supplier is not None
    assert order_view.supplier.name == "relcoma.com.ua"
    # кошторис групи — сума позицій
    assert order_view.cost_total == 400.0

    page = client.get(f"/procurements/{procurement_id}?group=order").text
    assert "Рахунок 14802" in page
    # позиція без замовлення отримує власну групу в кінці
    assert "Без замовлення" in page


def test_order_group_spans_modules(client: TestClient) -> None:
    """Замовлення — інша вісь, ніж модуль: одна група перетинає кілька модулів."""
    procurement_id, item_ids = _procurement_with_items(client, ["Кнопка", "Бек", "Балун"])
    client.post(
        f"/procurements/{procurement_id}/orders",
        data={"title": "Рахунок 5229", "item_ids": item_ids},
        follow_redirects=False,
    )

    grouped_by_order = client.get(f"/procurements/{procurement_id}?group=order").text
    grouped_by_module = client.get(f"/procurements/{procurement_id}").text
    assert grouped_by_order.count("Рахунок 5229") >= 1
    # у режимі модулів позиції лишаються в модулях, а замовлення видно чипом у рядку
    assert "order-chip" in grouped_by_module
    assert "🧩" in grouped_by_module


def test_order_stage_moves_all_items_with_history(client: TestClient, uow: UnitOfWork) -> None:
    procurement_id, item_ids = _procurement_with_items(client, ["Кнопка", "Запобіжник"])
    client.post(
        f"/procurements/{procurement_id}/orders",
        data={"title": "Рахунок 1", "item_ids": item_ids},
        follow_redirects=False,
    )

    response = client.post("/orders/1/stage", data={"stage": "paid"}, follow_redirects=False)
    assert response.status_code == 303

    details = uow.get_procurement_details(procurement_id)
    assert {v.item.stage.value for v in details.items} == {"paid"}
    assert details.orders[0].stage is not None
    assert details.orders[0].stage.value == "paid"
    # історія переходів пишеться по кожній позиції, тож дата «з …» не відстає
    assert all(v.stage_since is not None for v in details.items)
    assert all(
        step.stage.value == "paid"
        for step in uow.get_line_item_details(item_ids[0]).stage_timeline[-1:]
    )


def test_order_stage_is_mixed_when_items_differ(client: TestClient, uow: UnitOfWork) -> None:
    procurement_id, item_ids = _procurement_with_items(client, ["Кнопка", "Запобіжник"])
    client.post(
        f"/procurements/{procurement_id}/orders",
        data={"title": "Рахунок 1", "item_ids": item_ids},
        follow_redirects=False,
    )
    client.post(f"/items/{item_ids[0]}/stage", data={"stage": "paid"}, follow_redirects=False)

    assert uow.get_procurement_details(procurement_id).orders[0].stage is None
    assert "Змішана" in client.get(f"/procurements/{procurement_id}?group=order").text


def test_bulk_stage_for_selected_items(client: TestClient, uow: UnitOfWork) -> None:
    procurement_id, item_ids = _procurement_with_items(client, ["Кнопка", "Запобіжник", "Реле"])

    response = client.post(
        "/items/bulk-stage",
        data={"stage": "awaiting_invoice", "item_ids": item_ids[:2]},
        follow_redirects=False,
    )
    assert response.status_code == 303

    stages = {
        v.item.name: v.item.stage.value for v in uow.get_procurement_details(procurement_id).items
    }
    assert stages == {"Кнопка": "awaiting_invoice", "Запобіжник": "awaiting_invoice", "Реле": "new"}


def test_one_invoice_covers_every_item_of_the_order(client: TestClient, uow: UnitOfWork) -> None:
    """Головна причина фічі: один файл замість копії на кожну позицію."""
    procurement_id, item_ids = _procurement_with_items(client, ["Кнопка", "Запобіжник", "Реле"])
    client.post(
        f"/procurements/{procurement_id}/orders",
        data={"title": "Рахунок 14802", "item_ids": item_ids},
        follow_redirects=False,
    )

    upload = client.post(
        "/orders/1/documents",
        data={"title": "Рахунок 14802", "kind": "invoice", "amount": "1205"},
        files={"file": ("14802.pdf", b"%PDF-1.4 test", "application/pdf")},
        follow_redirects=False,
    )
    assert upload.status_code == 303

    details = uow.get_procurement_details(procurement_id)
    assert len(details.documents) == 1
    document = details.documents[0].document
    assert sorted(document.line_item_ids) == sorted(item_ids)
    assert details.orders[0].invoiced_total == 1205.0
    # рахунок видно на сторінці кожної позиції
    for item_id in item_ids:
        assert len(uow.get_line_item_details(item_id).documents) == 1


def test_assign_and_detach_items(client: TestClient, uow: UnitOfWork) -> None:
    procurement_id, item_ids = _procurement_with_items(client, ["Кнопка", "Запобіжник"])
    client.post(
        f"/procurements/{procurement_id}/orders",
        data={"title": "Рахунок 1", "item_ids": [item_ids[0]]},
        follow_redirects=False,
    )

    client.post(
        "/orders/assign", data={"order_id": "1", "item_ids": [item_ids[1]]}, follow_redirects=False
    )
    assert len(uow.get_procurement_details(procurement_id).orders[0].items) == 2

    client.post("/orders/detach", data={"item_ids": [item_ids[1]]}, follow_redirects=False)
    assert len(uow.get_procurement_details(procurement_id).orders[0].items) == 1


def test_delete_order_keeps_items_and_documents(client: TestClient, uow: UnitOfWork) -> None:
    procurement_id, item_ids = _procurement_with_items(client, ["Кнопка", "Запобіжник"])
    client.post(
        f"/procurements/{procurement_id}/orders",
        data={"title": "Рахунок 1", "item_ids": item_ids},
        follow_redirects=False,
    )
    client.post(
        "/orders/1/documents",
        data={"title": "Рахунок 1", "kind": "invoice"},
        files={"file": ("inv.pdf", b"%PDF-1.4", "application/pdf")},
        follow_redirects=False,
    )

    response = client.post("/orders/1/delete", follow_redirects=False)
    assert response.status_code == 303

    details = uow.get_procurement_details(procurement_id)
    assert details.orders == []
    assert len(details.items) == 2
    assert all(v.item.order_id is None for v in details.items)
    # документ лишається і далі привʼязаний до позицій
    assert len(details.documents) == 1
    assert sorted(details.documents[0].document.line_item_ids) == sorted(item_ids)


def test_order_filter_narrows_the_items_table(client: TestClient) -> None:
    procurement_id, item_ids = _procurement_with_items(client, ["Кнопка", "Запобіжник"])
    client.post(
        f"/procurements/{procurement_id}/orders",
        data={"title": "Рахунок 1", "item_ids": [item_ids[0]]},
        follow_redirects=False,
    )

    listing = client.get(f"/procurements/{procurement_id}?group=order&order=1").text.split(
        "Додати позицію"
    )[0]
    assert "Кнопка" in listing
    assert "Запобіжник" not in listing


def test_selected_items_cannot_cross_procurements(client: TestClient) -> None:
    procurement_id, item_ids = _procurement_with_items(client, ["Кнопка"])
    other = client.post("/procurements", data={"name": "Інша"}, follow_redirects=False)
    other_id = int(other.headers["location"].rsplit("/", 1)[-1])
    client.post(
        f"/procurements/{other_id}/items",
        data={"name": "Чужа позиція", "qty_required": "1"},
        follow_redirects=False,
    )
    client.post(
        f"/procurements/{procurement_id}/orders",
        data={"title": "Рахунок 1", "item_ids": item_ids},
        follow_redirects=False,
    )

    response = client.post(
        "/orders/assign", data={"order_id": "1", "item_ids": [2]}, follow_redirects=False
    )
    assert response.status_code == 422
