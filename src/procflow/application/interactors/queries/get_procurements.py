"""Queries for procurement list and details."""

from __future__ import annotations

from dataclasses import dataclass

from procflow.application.dto import (
    LineItemView,
    ProcurementDetails,
    ProcurementSummary,
)
from procflow.application.interfaces.repositories import (
    DocumentRepository,
    LineItemRepository,
    MessageRepository,
    OfferRepository,
    ProcurementRepository,
)


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

    def __call__(self, procurement_id: int) -> ProcurementDetails:
        procurement = self.procurements.get(procurement_id)
        item_views: list[LineItemView] = []
        for item in self.items.list_for_procurement(procurement_id):
            assert item.id is not None
            item_views.append(
                LineItemView(
                    item=item,
                    offers=self.offers.list_for_item(item.id),
                    last_message=self.messages.latest_for_item(item.id),
                )
            )
        return ProcurementDetails(
            procurement=procurement,
            items=item_views,
            documents=self.documents.search(procurement_id=procurement_id),
            cost_total=sum(v.item.total_price for v in item_views),
        )
