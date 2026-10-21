"""Одноразовий скрипт: зібрати замовлення з дублів рахунків.

До появи замовлень один рахунок на кілька позицій вантажили по разу на позицію —
у базі лежить N копій одного файлу. Скрипт знаходить такі групи (однакове
``original_name`` усередині закупівлі), створює на кожну замовлення, кладе туди
позиції і лишає один документ, привʼязаний до всіх них.

    uv run python scripts/seed_orders_from_duplicate_documents.py            # показати план
    uv run python scripts/seed_orders_from_duplicate_documents.py --apply    # виконати

Перед --apply зробіть копію data/procflow.db.
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from procflow.application.dto import (  # noqa: E402
    AttachDocumentInput,
    DocumentView,
    SupplierOrderInput,
)
from procflow.application.uow import UnitOfWork  # noqa: E402
from procflow.domain.entities import Supplier  # noqa: E402
from procflow.main.config import Settings  # noqa: E402
from procflow.main.container import build_container  # noqa: E402


def _duplicate_groups(documents: list[DocumentView]) -> dict[str, list[DocumentView]]:
    """Групи документів з однаковим іменем файлу, кожен — рівно на одну позицію."""
    by_name: dict[str, list[DocumentView]] = defaultdict(list)
    for view in documents:
        if view.document.order_id is None and len(view.document.line_item_ids) == 1:
            by_name[view.document.original_name].append(view)
    return {name: views for name, views in by_name.items() if len(views) > 1}


_GENERIC_TITLES = {"Рахунок", "Квитанція", "Накладна", "Документ", "Договір"}
_UUID_TAIL = re.compile(
    r"[_-]?[0-9a-f]{8}[-_][0-9a-f]{4}[-_][0-9a-f]{4}[-_][0-9a-f]{4}[-_][0-9a-f]{12}$"
)


def _title(original_name: str, views: list[DocumentView]) -> str:
    """Назва замовлення: осмислена назва документа, інакше — імʼя файлу без uuid."""
    specific = {v.document.title for v in views} - {original_name} - _GENERIC_TITLES
    if len(specific) == 1:
        return next(iter(specific))[:60]
    stem = _UUID_TAIL.sub("", Path(original_name).stem)
    return re.sub(r"\s+", " ", stem.replace("_", " ")).strip()[:60]


def _guess_supplier(uow: UnitOfWork, item_ids: list[int]) -> Supplier | None:
    """Продавець = той, що зустрічається в пропозиціях більшості позицій групи.

    why: у старих даних постачальник на документі майже завжди порожній, а от
    пропозиції по позиціях зазвичай ведуть на того самого продавця.
    """
    votes: Counter[int] = Counter()
    for item_id in item_ids:
        for _, supplier in uow.offers.list_for_item(item_id):
            if supplier.id is not None:
                votes[supplier.id] += 1
    if not votes:
        return None
    best, count = votes.most_common(1)[0]
    return uow.suppliers.get(best) if count > 1 else None


def main(apply: bool) -> None:
    container = build_container(Settings())
    with container.unit_of_work() as uow:
        for summary in uow.list_procurements():
            procurement_id = summary.procurement.id
            assert procurement_id is not None
            groups = _duplicate_groups(uow.documents.search(procurement_id=procurement_id))
            if not groups:
                continue
            print(f"\n=== {summary.procurement.name} ===")
            for name, views in groups.items():
                item_ids = [v.document.line_item_ids[0] for v in views]
                items = [uow.items.get(i) for i in item_ids]
                supplier = _guess_supplier(uow, item_ids)
                title = _title(name, views)
                print(f"  📦 {title} — {supplier.name if supplier else 'продавець невідомий'}")
                for item in items:
                    print(f"       · {item.name}")
                print(f"     {len(views)} копій документа «{name}» → 1")
                if not apply:
                    continue

                keeper = min(views, key=lambda v: v.document.id or 0).document
                content = uow.storage.absolute_path(keeper.file_path).read_bytes()
                order = uow.create_order(
                    procurement_id,
                    SupplierOrderInput(title=title, supplier_id=supplier.id if supplier else None),
                    item_ids,
                )
                uow.attach_document(
                    AttachDocumentInput(
                        procurement_id=procurement_id,
                        supplier_id=supplier.id if supplier else None,
                        payer_id=keeper.payer_id,
                        kind=keeper.kind,
                        title=title,
                        original_name=keeper.original_name,
                        content=content,
                        amount=keeper.amount,
                        doc_date=keeper.doc_date,
                        note=keeper.note,
                        order_id=order.id,
                        line_item_ids=item_ids,
                    )
                )
                for view in views:
                    assert view.document.id is not None
                    uow.delete_document(view.document.id)
    print("\nЗастосовано." if apply else "\nЦе був лише план. Запустіть з --apply, щоб виконати.")


if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
