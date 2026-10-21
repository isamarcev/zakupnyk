"""Grouping of line items for the procurement page and text exports.

Модуль («що це») і замовлення («чим одним рахунком купуємо») — дві незалежні осі
групування тих самих позицій, тому одна структура і одна функція на обидві.
"""

from __future__ import annotations

from procflow.application.dto import ItemGroup, LineItemView, OrderView

GROUP_MODES = ("module", "order", "flat")
LOOSE_KEY = "ord:none"


def build_groups(mode: str, items: list[LineItemView], orders: list[OrderView]) -> list[ItemGroup]:
    """Групи для режиму; порожній список — виводимо позиції плоско."""
    if mode == "order":
        return _order_groups(items, orders)
    if mode == "module":
        return _module_groups(items)
    return []


def sort_for_orders(items: list[LineItemView], orders: list[OrderView]) -> list[LineItemView]:
    """Позиції одного замовлення поруч — інакше групи в таблиці розсипаються."""
    position = {view.order.id: index for index, view in enumerate(orders)}
    return sorted(
        items,
        key=lambda v: (
            v.item.order_id is None,
            position.get(v.item.order_id, 0),
            v.item.id or 0,
        ),
    )


def _module_groups(items: list[LineItemView]) -> list[ItemGroup]:
    """Групи за модулем у порядку першої появи; без модулів — груп немає."""
    if not any(v.item.module for v in items):
        return []
    groups: dict[str | None, ItemGroup] = {}
    for view in items:
        module = view.item.module
        group = groups.get(module)
        if group is None:
            group = ItemGroup(key=f"mod:{module or ''}", label=module or "Без модуля", icon="🧩")
            groups[module] = group
        group.items.append(view)
    return list(groups.values())


def _order_groups(items: list[LineItemView], orders: list[OrderView]) -> list[ItemGroup]:
    """Групи за замовленнями (у порядку створення), позиції без замовлення — в кінці."""
    by_order: dict[int | None, list[LineItemView]] = {}
    for view in items:
        by_order.setdefault(view.item.order_id, []).append(view)
    groups = [
        ItemGroup(
            key=f"ord:{view.order.id}",
            label=view.order.display_title(),
            icon="📦",
            items=by_order[view.order.id],
            order=view,
        )
        for view in orders
        if by_order.get(view.order.id)
    ]
    loose = by_order.get(None)
    if loose:
        groups.append(ItemGroup(key=LOOSE_KEY, label="Без замовлення", icon="•", items=loose))
    return groups
