"""Query: full details of a single line item (offers, documents, messages)."""

from __future__ import annotations

from dataclasses import dataclass

from procflow.application.dto import LineItemDetails
from procflow.application.interfaces.repositories import (
    DocumentRepository,
    LineItemRepository,
    MessageRepository,
    OfferRepository,
    ProcurementRepository,
)


@dataclass(slots=True)
class GetLineItemDetails:
    items: LineItemRepository
    procurements: ProcurementRepository
    offers: OfferRepository
    documents: DocumentRepository
    messages: MessageRepository

    def __call__(self, item_id: int) -> LineItemDetails:
        item = self.items.get(item_id)
        all_docs = self.documents.search(procurement_id=item.procurement_id)
        item_docs = [v for v in all_docs if item_id in v.document.line_item_ids]
        return LineItemDetails(
            item=item,
            procurement=self.procurements.get(item.procurement_id),
            offers=self.offers.list_for_item(item_id),
            documents=item_docs,
            messages=self.messages.list_for_item(item_id),
        )
