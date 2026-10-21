"""Query: pack documents of the filtered items into one flat archive."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from procflow.application.dto import (
    DocumentView,
    ExportBundle,
    ExportEntry,
    ItemGroup,
    LineItemView,
    ProcurementDetails,
)
from procflow.application.formatting import money, qty
from procflow.application.interactors.queries.get_procurements import GetProcurementDetails
from procflow.application.interactors.queries.group_items import build_groups, sort_for_orders
from procflow.domain.entities import DocumentKind, ItemStage

LISTING_NAME = "_перелік.txt"

# why: у назві архіву множина читається природніше за ярлик сутності («рахунки», не «рахунок»)
_PLURAL = {
    DocumentKind.INVOICE: "рахунки",
    DocumentKind.WAYBILL: "накладні",
    DocumentKind.CONTRACT: "договори",
    DocumentKind.OTHER: "інші документи",
}


def _safe(value: str) -> str:
    """Імʼя, безпечне для будь-якої файлової системи всередині архіву."""
    cleaned = "".join("_" if ch in '\\/:*?"<>|' or ord(ch) < 32 else ch for ch in value).strip()
    return cleaned.strip(". ")[:90] or "документ"


@dataclass(slots=True)
class ExportProcurementDocuments:
    """Плоский архів документів + специфікація позицій у `_перелік.txt`.

    Фільтри ті самі, що й у таблиці позицій (стадії, замовлення, вибрані галочками
    позиції, режим групування), плюс тип документа — щоб вивантажити самі рахунки.
    """

    details: GetProcurementDetails

    def __call__(
        self,
        procurement_id: int,
        *,
        stages: set[ItemStage] | None = None,
        order_id: int | None = None,
        item_ids: list[int] | None = None,
        kinds: set[DocumentKind] | None = None,
        group: str = "module",
    ) -> ExportBundle:
        details = self.details(procurement_id)
        items = _visible_items(details, stages or set(), order_id, item_ids or [])
        if group == "order":
            items = sort_for_orders(items, details.orders)
        visible_ids = {v.item.id for v in items}
        visible_orders: set[int | None] = {v.item.order_id for v in items if v.item.order_id}
        documents = [
            doc
            for doc in sorted(details.documents, key=lambda d: d.document.id or 0)
            if (not kinds or doc.document.kind in kinds)
            and _belongs(doc, visible_ids, visible_orders)
        ]
        used: set[str] = set()
        return ExportBundle(
            filename=_archive_name(details, kinds),
            entries=[_entry(doc, used) for doc in documents],
            listing=_listing(items, build_groups(group, items, details.orders)),
        )


def _visible_items(
    details: ProcurementDetails,
    stages: set[ItemStage],
    order_id: int | None,
    item_ids: list[int],
) -> list[LineItemView]:
    chosen = set(item_ids)
    return [
        v
        for v in details.items
        if (not stages or v.item.stage in stages)
        and (order_id is None or v.item.order_id == order_id)
        and (not chosen or v.item.id in chosen)
    ]


def _belongs(doc: DocumentView, item_ids: set[int | None], order_ids: set[int | None]) -> bool:
    return doc.document.order_id in order_ids or bool(
        item_ids.intersection(doc.document.line_item_ids)
    )


def _listing(items: list[LineItemView], groups: list[ItemGroup]) -> str:
    """Специфікація позицій — те саме, що блок «Специфікація» на сторінці.

    why: групи нумеруються («Група 1»), а не називаються — у режимі замовлень
    заголовком був би номер рахунка, який одержувачу списку ні про що не каже.
    """
    blocks: list[str] = []
    for index, group in enumerate(groups, start=1):
        title = f"Група {index}"
        lines = [title, *(_item_line(v) for v in group.items)]
        lines.append(f"Підсумок «{title}»: {money(group.cost_total)} грн ({len(group.items)} поз.)")
        blocks.append("\n".join(lines))
    if not groups:
        blocks.append("\n".join(_item_line(v) for v in items))
    blocks.append(f"Разом: {money(sum(v.item.total_price for v in items))} грн")
    # why: групи розділяємо порожнім рядком — суцільна стіна рядків не читається
    return "\n\n".join(block for block in blocks if block) + "\n"


def _item_line(view: LineItemView) -> str:
    item = view.item
    return (
        f"{item.name} — {qty(item.qty_required)} шт, "
        f"ціна {money(item.unit_price)}, сума {money(item.total_price)} грн"
    )


def _archive_name(details: ProcurementDetails, kinds: set[DocumentKind] | None) -> str:
    # why: next(iter(...)), а не pop() — set приходить від виклику й не наш, щоб його псувати
    what = _PLURAL[next(iter(kinds))] if kinds and len(kinds) == 1 else "документи"
    return f"{_safe(details.procurement.name)} — {what}.zip"


def _entry(doc: DocumentView, used: set[str]) -> ExportEntry:
    """Імʼя всередині архіву; повтори розводяться суфіксом (2), (3)…"""
    name = PurePosixPath(_safe(doc.document.original_name))
    arcname = str(name)
    counter = 2
    while arcname in used:
        arcname = f"{name.stem} ({counter}){name.suffix}"
        counter += 1
    used.add(arcname)
    return ExportEntry(arcname=arcname, file_path=doc.document.file_path)
