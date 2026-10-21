"""SQLAlchemy implementation of the supplier order repository."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from procflow.domain.entities import SupplierOrder
from procflow.domain.exceptions import SupplierOrderNotFoundError
from procflow.infrastructure.database import DocumentRow, LineItemRow, SupplierOrderRow
from procflow.infrastructure.repositories.mappers import supplier_order_from_row


@dataclass(slots=True)
class SqlSupplierOrderRepository:
    session: Session

    def add(self, order: SupplierOrder) -> SupplierOrder:
        row = SupplierOrderRow(
            procurement_id=order.procurement_id,
            supplier_id=order.supplier_id,
            title=order.title,
            note=order.note,
            created_at=order.created_at,
        )
        self.session.add(row)
        self.session.flush()
        order.id = row.id
        return order

    def get(self, order_id: int) -> SupplierOrder:
        row = self.session.get(SupplierOrderRow, order_id)
        if row is None:
            raise SupplierOrderNotFoundError(f"Замовлення #{order_id} не знайдено")
        return supplier_order_from_row(row)

    def list_for_procurement(self, procurement_id: int) -> list[SupplierOrder]:
        rows = self.session.scalars(
            select(SupplierOrderRow)
            .where(SupplierOrderRow.procurement_id == procurement_id)
            .order_by(SupplierOrderRow.id)
        )
        return [supplier_order_from_row(r) for r in rows]

    def update(self, order: SupplierOrder) -> None:
        assert order.id is not None
        row = self.session.get(SupplierOrderRow, order.id)
        if row is None:
            raise SupplierOrderNotFoundError(f"Замовлення #{order.id} не знайдено")
        row.title = order.title
        row.supplier_id = order.supplier_id
        row.note = order.note
        self.session.flush()

    def delete(self, order_id: int) -> None:
        row = self.session.get(SupplierOrderRow, order_id)
        if row is None:
            raise SupplierOrderNotFoundError(f"Замовлення #{order_id} не знайдено")
        # why: позиції та документи переживають замовлення — лише відвʼязуємо їх,
        # не покладаючись на ON DELETE SET NULL (старі БД створені без цього FK).
        self.session.execute(
            update(LineItemRow).where(LineItemRow.order_id == order_id).values(order_id=None)
        )
        self.session.execute(
            update(DocumentRow).where(DocumentRow.order_id == order_id).values(order_id=None)
        )
        self.session.delete(row)
        self.session.flush()
