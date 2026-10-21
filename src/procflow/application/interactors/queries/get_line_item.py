"""Query: full details of a single line item (offers, documents, messages)."""

from __future__ import annotations

from dataclasses import dataclass

from procflow.application.dto import LineItemDetails, StageStep
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


def _timeline(item: LineItem, changes: list[StageChange]) -> list[StageStep]:
    """Хронологія стадій: створення (завжди «Нове») + зафіксовані переходи.

    why: історія ведеться не з першого дня, тож якщо поточна стадія в неї не
    потрапила — показуємо її останнім кроком без дати, а не приховуємо.
    """
    steps = [StageStep(stage=ItemStage.NEW, at=item.created_at)]
    steps += [StageStep(stage=c.stage, at=c.changed_at) for c in changes]
    if steps[-1].stage is not item.stage:
        steps.append(StageStep(stage=item.stage, at=None))
    return steps


@dataclass(slots=True)
class GetLineItemDetails:
    items: LineItemRepository
    procurements: ProcurementRepository
    offers: OfferRepository
    documents: DocumentRepository
    messages: MessageRepository
    stage_changes: StageChangeRepository
    orders: SupplierOrderRepository
    suppliers: SupplierRepository

    def __call__(self, item_id: int) -> LineItemDetails:
        item = self.items.get(item_id)
        all_docs = self.documents.search(procurement_id=item.procurement_id)
        item_docs = [v for v in all_docs if item_id in v.document.line_item_ids]
        order = self.orders.get(item.order_id) if item.order_id is not None else None
        order_supplier = (
            self.suppliers.get(order.supplier_id)
            if order is not None and order.supplier_id is not None
            else None
        )
        return LineItemDetails(
            item=item,
            procurement=self.procurements.get(item.procurement_id),
            offers=self.offers.list_for_item(item_id),
            documents=item_docs,
            messages=self.messages.list_for_item(item_id),
            stage_timeline=_timeline(item, self.stage_changes.list_for_item(item_id)),
            order=order,
            order_supplier=order_supplier,
        )
