"""Commands for supplier orders: group positions bought by one invoice."""

from __future__ import annotations

from dataclasses import dataclass

from procflow.application.dto import SupplierOrderInput
from procflow.application.interactors.commands.manage_procurements import SetItemStage
from procflow.application.interactors.commands.manage_suppliers import ResolveSupplier
from procflow.application.interfaces.repositories import (
    LineItemRepository,
    ProcurementRepository,
    StageChangeRepository,
    SupplierOrderRepository,
    SupplierRepository,
)
from procflow.domain.entities import ItemStage, LineItem, SupplierOrder
from procflow.domain.exceptions import InvalidInputError


@dataclass(slots=True)
class CreateSupplierOrder:
    """Створює замовлення і (за бажанням) одразу кладе в нього вибрані позиції."""

    orders: SupplierOrderRepository
    procurements: ProcurementRepository
    items: LineItemRepository
    suppliers: SupplierRepository

    def __call__(
        self, procurement_id: int, data: SupplierOrderInput, item_ids: list[int]
    ) -> SupplierOrder:
        self.procurements.get(procurement_id)  # raises if missing
        resolve = ResolveSupplier(self.suppliers)
        order = self.orders.add(
            SupplierOrder(
                id=None,
                procurement_id=procurement_id,
                title=data.title.strip(),
                supplier_id=resolve(
                    data.supplier_id, data.new_supplier_name, data.new_supplier_source
                ),
                note=data.note.strip(),
            )
        )
        assert order.id is not None
        if item_ids:
            AssignItemsToOrder(self.orders, self.items)(order.id, item_ids)
        return order


@dataclass(slots=True)
class UpdateSupplierOrder:
    orders: SupplierOrderRepository
    suppliers: SupplierRepository

    def __call__(self, order_id: int, data: SupplierOrderInput) -> SupplierOrder:
        order = self.orders.get(order_id)
        order.title = data.title.strip()
        order.supplier_id = ResolveSupplier(self.suppliers)(
            data.supplier_id, data.new_supplier_name, data.new_supplier_source
        )
        order.note = data.note.strip()
        self.orders.update(order)
        return order


@dataclass(slots=True)
class DeleteSupplierOrder:
    """Видаляє групу; позиції та документи лишаються, лише відвʼязуються."""

    orders: SupplierOrderRepository

    def __call__(self, order_id: int) -> int:
        procurement_id = self.orders.get(order_id).procurement_id
        self.orders.delete(order_id)
        return procurement_id


@dataclass(slots=True)
class AssignItemsToOrder:
    orders: SupplierOrderRepository
    items: LineItemRepository

    def __call__(self, order_id: int, item_ids: list[int]) -> SupplierOrder:
        order = self.orders.get(order_id)
        for item_id in item_ids:
            item = self.items.get(item_id)
            if item.procurement_id != order.procurement_id:
                # why: замовлення живе всередині закупівлі — інакше кошторис і
                # фільтри сторінки почали б показувати чужі позиції.
                raise InvalidInputError("Позиція з іншої закупівлі не може увійти в замовлення")
        self.items.set_order(item_ids, order_id)
        return order


@dataclass(slots=True)
class DetachItemsFromOrder:
    items: LineItemRepository

    def __call__(self, item_ids: list[int]) -> None:
        for item_id in item_ids:
            self.items.get(item_id)  # raises if missing
        self.items.set_order(item_ids, None)


@dataclass(slots=True)
class SetItemsStage:
    """Масова зміна стадії: по одній позиції, щоб історія переходів писалась.

    why: правило з item_stage_changes — будь-яка зміна стадії лишає слід, інакше
    дата «з …» у таблиці почне відставати від реальності.
    """

    items: LineItemRepository
    stage_changes: StageChangeRepository

    def __call__(self, item_ids: list[int], stage: ItemStage) -> list[LineItem]:
        if not item_ids:
            raise InvalidInputError("Не вибрано жодної позиції")
        set_one = SetItemStage(self.items, self.stage_changes)
        return [set_one(item_id, stage) for item_id in item_ids]


@dataclass(slots=True)
class SetOrderStage:
    """Стадія замовлення = стадія всіх його позицій (одним кліком)."""

    orders: SupplierOrderRepository
    items: LineItemRepository
    stage_changes: StageChangeRepository

    def __call__(self, order_id: int, stage: ItemStage) -> SupplierOrder:
        order = self.orders.get(order_id)
        item_ids = [
            i.id
            for i in self.items.list_for_procurement(order.procurement_id)
            if i.order_id == order_id and i.id is not None
        ]
        if item_ids:
            SetItemsStage(self.items, self.stage_changes)(item_ids, stage)
        return order
