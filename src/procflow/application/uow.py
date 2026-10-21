"""Unit of work: all use-cases over one transactional repository set.

Depends only on repository/storage interfaces; concrete wiring happens in main.
Presentation receives this object per request and calls interactors.
"""

from __future__ import annotations

from dataclasses import dataclass

from procflow.application.interactors.commands.import_needs import ImportNeeds
from procflow.application.interactors.commands.manage_documents import (
    AttachDocument,
    DeleteDocument,
)
from procflow.application.interactors.commands.manage_messages import (
    AddMessage,
    DeleteMessage,
)
from procflow.application.interactors.commands.manage_orders import (
    AssignItemsToOrder,
    CreateSupplierOrder,
    DeleteSupplierOrder,
    DetachItemsFromOrder,
    SetItemsStage,
    SetOrderStage,
    UpdateSupplierOrder,
)
from procflow.application.interactors.commands.manage_payers import (
    CreatePayer,
    DeletePayer,
    ListPayers,
    UpdatePayer,
)
from procflow.application.interactors.commands.manage_procurements import (
    AddLineItem,
    CreateProcurement,
    DeleteLineItem,
    DeleteProcurement,
    SetItemStage,
    UpdateLineItem,
    UpdateProcurement,
)
from procflow.application.interactors.commands.manage_recipients import (
    CreateRecipient,
    DeleteRecipient,
    ListRecipients,
    UpdateRecipient,
)
from procflow.application.interactors.commands.manage_suppliers import (
    AddOffer,
    CreateSupplier,
    DeleteOffer,
    ResolveSupplier,
    UpdateSupplier,
)
from procflow.application.interactors.queries.export_documents import (
    ExportProcurementDocuments,
)
from procflow.application.interactors.queries.get_line_item import GetLineItemDetails
from procflow.application.interactors.queries.get_procurements import (
    GetProcurementDetails,
    ListProcurements,
)
from procflow.application.interactors.queries.get_suppliers import (
    GetSupplierDetails,
    ListSuppliers,
)
from procflow.application.interactors.queries.search_documents import SearchDocuments
from procflow.application.interfaces import FileStorage, NeedsParser
from procflow.application.interfaces.repositories import (
    DocumentRepository,
    LineItemRepository,
    MessageRepository,
    OfferRepository,
    PayerRepository,
    ProcurementRepository,
    RecipientRepository,
    StageChangeRepository,
    SupplierOrderRepository,
    SupplierRepository,
)


@dataclass(slots=True)
class UnitOfWork:
    """Interactor factory bound to one repository set (one DB transaction)."""

    procurements: ProcurementRepository
    items: LineItemRepository
    suppliers: SupplierRepository
    offers: OfferRepository
    documents: DocumentRepository
    payers: PayerRepository
    recipients: RecipientRepository
    messages: MessageRepository
    stage_changes: StageChangeRepository
    orders: SupplierOrderRepository
    storage: FileStorage
    needs_parser: NeedsParser

    # ------------------------------------------------------------- commands
    @property
    def create_procurement(self) -> CreateProcurement:
        return CreateProcurement(self.procurements)

    @property
    def update_procurement(self) -> UpdateProcurement:
        return UpdateProcurement(self.procurements)

    @property
    def delete_procurement(self) -> DeleteProcurement:
        return DeleteProcurement(self.procurements)

    @property
    def add_line_item(self) -> AddLineItem:
        return AddLineItem(self.procurements, self.items)

    @property
    def update_line_item(self) -> UpdateLineItem:
        return UpdateLineItem(self.items)

    @property
    def delete_line_item(self) -> DeleteLineItem:
        return DeleteLineItem(self.items)

    @property
    def set_item_stage(self) -> SetItemStage:
        return SetItemStage(self.items, self.stage_changes)

    @property
    def create_order(self) -> CreateSupplierOrder:
        return CreateSupplierOrder(self.orders, self.procurements, self.items, self.suppliers)

    @property
    def update_order(self) -> UpdateSupplierOrder:
        return UpdateSupplierOrder(self.orders, self.suppliers)

    @property
    def delete_order(self) -> DeleteSupplierOrder:
        return DeleteSupplierOrder(self.orders)

    @property
    def assign_items_to_order(self) -> AssignItemsToOrder:
        return AssignItemsToOrder(self.orders, self.items)

    @property
    def detach_items_from_order(self) -> DetachItemsFromOrder:
        return DetachItemsFromOrder(self.items)

    @property
    def set_items_stage(self) -> SetItemsStage:
        return SetItemsStage(self.items, self.stage_changes)

    @property
    def set_order_stage(self) -> SetOrderStage:
        return SetOrderStage(self.orders, self.items, self.stage_changes)

    @property
    def resolve_supplier(self) -> ResolveSupplier:
        return ResolveSupplier(self.suppliers)

    @property
    def create_supplier(self) -> CreateSupplier:
        return CreateSupplier(self.suppliers)

    @property
    def update_supplier(self) -> UpdateSupplier:
        return UpdateSupplier(self.suppliers)

    @property
    def add_offer(self) -> AddOffer:
        return AddOffer(self.offers, self.items, self.suppliers)

    @property
    def delete_offer(self) -> DeleteOffer:
        return DeleteOffer(self.offers)

    @property
    def attach_document(self) -> AttachDocument:
        return AttachDocument(
            self.documents, self.procurements, self.suppliers, self.payers, self.storage
        )

    @property
    def delete_document(self) -> DeleteDocument:
        return DeleteDocument(self.documents, self.storage)

    @property
    def create_payer(self) -> CreatePayer:
        return CreatePayer(self.payers)

    @property
    def update_payer(self) -> UpdatePayer:
        return UpdatePayer(self.payers)

    @property
    def delete_payer(self) -> DeletePayer:
        return DeletePayer(self.payers)

    @property
    def import_needs(self) -> ImportNeeds:
        return ImportNeeds(self.procurements, self.items, self.suppliers, self.offers)

    # ------------------------------------------------------------- queries
    @property
    def list_procurements(self) -> ListProcurements:
        return ListProcurements(self.procurements, self.items, self.documents)

    @property
    def get_procurement_details(self) -> GetProcurementDetails:
        return GetProcurementDetails(
            self.procurements,
            self.items,
            self.offers,
            self.documents,
            self.messages,
            self.stage_changes,
            self.orders,
            self.suppliers,
        )

    @property
    def export_documents(self) -> ExportProcurementDocuments:
        return ExportProcurementDocuments(self.get_procurement_details)

    @property
    def get_line_item_details(self) -> GetLineItemDetails:
        return GetLineItemDetails(
            self.items,
            self.procurements,
            self.offers,
            self.documents,
            self.messages,
            self.stage_changes,
            self.orders,
            self.suppliers,
        )

    @property
    def add_message(self) -> AddMessage:
        return AddMessage(self.messages, self.items)

    @property
    def delete_message(self) -> DeleteMessage:
        return DeleteMessage(self.messages)

    @property
    def list_suppliers(self) -> ListSuppliers:
        return ListSuppliers(self.suppliers)

    @property
    def get_supplier_details(self) -> GetSupplierDetails:
        return GetSupplierDetails(self.suppliers, self.offers, self.documents)

    @property
    def search_documents(self) -> SearchDocuments:
        return SearchDocuments(self.documents)

    @property
    def list_payers(self) -> ListPayers:
        return ListPayers(self.payers)

    @property
    def create_recipient(self) -> CreateRecipient:
        return CreateRecipient(self.recipients)

    @property
    def update_recipient(self) -> UpdateRecipient:
        return UpdateRecipient(self.recipients)

    @property
    def delete_recipient(self) -> DeleteRecipient:
        return DeleteRecipient(self.recipients)

    @property
    def list_recipients(self) -> ListRecipients:
        return ListRecipients(self.recipients)
