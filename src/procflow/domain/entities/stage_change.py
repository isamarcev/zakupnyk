"""Stage change entity: one recorded transition of a line item's stage."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from procflow.domain.entities.procurement import ItemStage


@dataclass(slots=True)
class StageChange:
    """A line item entered ``stage`` at ``changed_at``.

    why: сама позиція зберігає лише поточну стадію, а користувачу потрібно бачити,
    коли вона такою стала (і як рухалась раніше).
    """

    id: int | None
    line_item_id: int
    stage: ItemStage
    changed_at: datetime = field(default_factory=datetime.now)
