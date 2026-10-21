"""Queries for procurement list and details."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from procflow.application.dto import (
    LineItemView,
    OrderView,
    ProcurementDetails,
    ProcurementSummary,
)
from procflow.application.interfaces.repositories import (
    DocumentRepository,
    LineItemRepository,
    MessageRepository,
    OfferRepository,
    ProcurementRepository,
    StageChangeRepository,
    SupplierOrderRepository,
    SupplierRepository,
)
from procflow.domain.entities import ItemStage, LineItem, StageChange


def stage_since(item: LineItem, latest: StageChange | None) -> datetime | None:
    """Коли позиція стала в поточну стадію.

    why: історія ведеться з моменту появи фічі, тож для «Нове» падаємо назад на
    дату створення позиції, а для старих позицій в іншій стадії чесно кажемо «невідомо».
    """
    if latest is not None and latest.stage is item.stage:
        return latest.changed_at
    if item.stage is ItemStage.NEW:
        return item.created_at
    return None


@dataclass(slots=True)
class ListProcurements:
    procurements: ProcurementRepository
    items: LineItemRepository
    documents: DocumentRepository

    def __call__(self) -> list[ProcurementSummary]:
        result: list[ProcurementSummary] = []
        for procurement in self.procurements.list_all():
            assert procurement.id is not None
            items = self.items.list_for_procurement(procurement.id)
            docs = self.documents.search(procurement_id=procurement.id)
            result.append(
                ProcurementSummary(
                    procurement=procurement,
                    items_total=len(items),
                    items_complete=sum(1 for i in items if i.is_complete),
                    cost_total=sum(i.total_price for i in items),
                    documents_count=len(docs),
                )
            )
        return result


@dataclass(slots=True)
class GetProcurementDetails:
    procurements: ProcurementRepository
    items: LineItemRepository
    offers: OfferRepository
    documents: DocumentRepository
    messages: MessageRepository
    stage_changes: StageChangeRepository
    orders: SupplierOrderRepository
    suppliers: SupplierRepository

    def __call__(self, procurement_id: int) -> ProcurementDetails:
        procurement = self.procurements.get(procurement_id)
        items = self.items.list_for_procurement(procurement_id)
        latest_changes = self.stage_changes.latest_for_items(
            [i.id for i in items if i.id is not None]
        )
        orders = self.orders.list_for_procurement(procurement_id)
        orders_by_id = {o.id: o for o in orders}
        item_views: list[LineItemView] = []
        for item in items:
            assert item.id is not None
            item_views.append(
                LineItemView(
                    item=item,
                    offers=self.offers.list_for_item(item.id),
                    last_message=self.messages.latest_for_item(item.id),
                    stage_since=stage_since(item, latest_changes.get(item.id)),
                    order=orders_by_id.get(item.order_id),
                )
            )
        documents = self.documents.search(procurement_id=procurement_id)
        # why: постачальників читаємо одним списком, щоб не робити запит на кожне
        # замовлення (сторінка й так тягне позиції, пропозиції та документи).
        suppliers_by_id = {s.id: s for s in self.suppliers.list_all()}
        order_views = [
            OrderView(
                order=order,
                supplier=suppliers_by_id.get(order.supplier_id),
                items=[v for v in item_views if v.item.order_id == order.id],
                documents=[v for v in documents if v.document.order_id == order.id],
            )
            for order in orders
        ]
        return ProcurementDetails(
            procurement=procurement,
            items=item_views,
            documents=documents,
            cost_total=sum(v.item.total_price for v in item_views),
            orders=order_views,
        )
