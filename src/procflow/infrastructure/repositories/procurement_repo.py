"""SQLAlchemy implementations of procurement and line-item repositories."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from procflow.domain.entities import LineItem, Procurement
from procflow.domain.exceptions import LineItemNotFoundError, ProcurementNotFoundError
from procflow.infrastructure.database import LineItemRow, ProcurementRow
from procflow.infrastructure.repositories.mappers import (
    line_item_from_row,
    procurement_from_row,
)


@dataclass(slots=True)
class SqlProcurementRepository:
    session: Session

    def add(self, procurement: Procurement) -> Procurement:
        row = ProcurementRow(
            name=procurement.name,
            description=procurement.description,
            status=procurement.status.value,
            created_at=procurement.created_at,
            updated_at=procurement.updated_at,
        )
        self.session.add(row)
        self.session.flush()
        procurement.id = row.id
        return procurement

    def get(self, procurement_id: int) -> Procurement:
        row = self.session.get(ProcurementRow, procurement_id)
        if row is None:
            raise ProcurementNotFoundError(f"Закупівлю #{procurement_id} не знайдено")
        return procurement_from_row(row)

    def list_all(self) -> list[Procurement]:
        rows = self.session.scalars(
            select(ProcurementRow).order_by(ProcurementRow.created_at.desc())
        )
        return [procurement_from_row(r) for r in rows]

    def update(self, procurement: Procurement) -> None:
        assert procurement.id is not None
        row = self.session.get(ProcurementRow, procurement.id)
        if row is None:
            raise ProcurementNotFoundError(f"Закупівлю #{procurement.id} не знайдено")
        row.name = procurement.name
        row.description = procurement.description
        row.status = procurement.status.value
        row.updated_at = procurement.updated_at
        self.session.flush()

    def delete(self, procurement_id: int) -> None:
        row = self.session.get(ProcurementRow, procurement_id)
        if row is None:
            raise ProcurementNotFoundError(f"Закупівлю #{procurement_id} не знайдено")
        self.session.delete(row)
        self.session.flush()


@dataclass(slots=True)
class SqlLineItemRepository:
    session: Session

    def add(self, item: LineItem) -> LineItem:
        row = LineItemRow(
            procurement_id=item.procurement_id,
            name=item.name,
            specification=item.specification,
            qty_required=item.qty_required,
            qty_ordered=item.qty_ordered,
            qty_in_progress=item.qty_in_progress,
            unit_price=item.unit_price,
            stage=item.stage.value,
            module=item.module,
            created_at=item.created_at,
        )
        self.session.add(row)
        self.session.flush()
        item.id = row.id
        return item

    def get(self, item_id: int) -> LineItem:
        row = self.session.get(LineItemRow, item_id)
        if row is None:
            raise LineItemNotFoundError(f"Позицію #{item_id} не знайдено")
        return line_item_from_row(row)

    def list_for_procurement(self, procurement_id: int) -> list[LineItem]:
        rows = self.session.scalars(
            select(LineItemRow)
            .where(LineItemRow.procurement_id == procurement_id)
            .order_by(LineItemRow.id)
        )
        return [line_item_from_row(r) for r in rows]

    def update(self, item: LineItem) -> None:
        assert item.id is not None
        row = self.session.get(LineItemRow, item.id)
        if row is None:
            raise LineItemNotFoundError(f"Позицію #{item.id} не знайдено")
        row.name = item.name
        row.specification = item.specification
        row.qty_required = item.qty_required
        row.qty_ordered = item.qty_ordered
        row.qty_in_progress = item.qty_in_progress
        row.unit_price = item.unit_price
        row.stage = item.stage.value
        row.module = item.module
        self.session.flush()

    def delete(self, item_id: int) -> None:
        row = self.session.get(LineItemRow, item_id)
        if row is None:
            raise LineItemNotFoundError(f"Позицію #{item_id} не знайдено")
        self.session.delete(row)
        self.session.flush()
