"""SQLAlchemy implementation of the stage change repository."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from procflow.domain.entities import StageChange
from procflow.infrastructure.database import StageChangeRow
from procflow.infrastructure.repositories.mappers import stage_change_from_row


@dataclass(slots=True)
class SqlStageChangeRepository:
    session: Session

    def add(self, change: StageChange) -> StageChange:
        row = StageChangeRow(
            line_item_id=change.line_item_id,
            stage=change.stage.value,
            changed_at=change.changed_at,
        )
        self.session.add(row)
        self.session.flush()
        change.id = row.id
        return change

    def list_for_item(self, line_item_id: int) -> list[StageChange]:
        rows = self.session.scalars(
            select(StageChangeRow)
            .where(StageChangeRow.line_item_id == line_item_id)
            .order_by(StageChangeRow.changed_at, StageChangeRow.id)
        )
        return [stage_change_from_row(r) for r in rows]

    def latest_for_items(self, line_item_ids: list[int]) -> dict[int, StageChange]:
        if not line_item_ids:
            return {}
        # why: переходів на позицію одиниці, тож дешевше прочитати їх одним
        # запитом по зростанню і лишити останній, ніж будувати віконний запит.
        rows = self.session.scalars(
            select(StageChangeRow)
            .where(StageChangeRow.line_item_id.in_(line_item_ids))
            .order_by(StageChangeRow.changed_at, StageChangeRow.id)
        )
        return {r.line_item_id: stage_change_from_row(r) for r in rows}
