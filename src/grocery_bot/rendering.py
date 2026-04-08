from dataclasses import dataclass

from grocery_bot.models import GroceryItem, GroceryItemStatus


@dataclass(slots=True, frozen=True)
class InlineKeyboardButton:
    text: str
    callback_data: str


@dataclass(slots=True, frozen=True)
class InlineKeyboardMarkup:
    inline_keyboard: list[list[InlineKeyboardButton]]


def render_list_text(items: list[GroceryItem]) -> str:
    active_items = [item for item in items if item.status == GroceryItemStatus.ACTIVE]
    done_items = [item for item in items if item.status == GroceryItemStatus.DONE]

    active_lines = [f"- {item.text}" for item in active_items] or ["• Пока пусто."]
    done_lines = [f"- {item.text}" for item in done_items] or ["• Пока ничего не куплено."]

    return "\n".join(
        [
            "Список покупок",
            "Нужно купить",
            *active_lines,
            "",
            "Куплено",
            *done_lines,
        ]
    )


def build_list_keyboard(items: list[GroceryItem]) -> InlineKeyboardMarkup:
    rows = [
        _build_item_row(item)
        for item in items
    ]
    if any(item.status == GroceryItemStatus.DONE for item in items):
        rows.append([InlineKeyboardButton(text="Очистить купленное", callback_data="clear_done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _build_item_row(item: GroceryItem) -> list[InlineKeyboardButton]:
    if item.status == GroceryItemStatus.DONE:
        return [
            InlineKeyboardButton(text="Вернуть", callback_data=f"return:{item.item_id}"),
            InlineKeyboardButton(text="Удалить", callback_data=f"delete:{item.item_id}"),
        ]

    return [
        InlineKeyboardButton(text="Куплено", callback_data=f"done:{item.item_id}"),
        InlineKeyboardButton(text="Удалить", callback_data=f"delete:{item.item_id}"),
    ]
