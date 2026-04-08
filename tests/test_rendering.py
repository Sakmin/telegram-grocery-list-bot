from grocery_bot.models import GroceryItem, GroceryItemStatus
from grocery_bot.rendering import build_list_keyboard, render_list_text


DONE_ITEM = GroceryItem(
    item_id=2,
    group_id=1,
    text="Bread",
    created_by_user_id=1,
    status=GroceryItemStatus.DONE,
)


def test_render_list_text_shows_short_empty_state():
    assert render_list_text([]) == "Список покупок\nПока ничего не добавлено."


def test_render_list_text_shows_short_bought_section_when_only_done_items():
    assert render_list_text([DONE_ITEM]) == "Список покупок\nПока ничего не добавлено.\n\nКуплено:"


def test_build_list_keyboard_puts_item_label_in_first_button_and_adds_clear_row():
    items = [
        GroceryItem(item_id=1, group_id=1, text="Milk", created_by_user_id=1),
        DONE_ITEM,
    ]

    keyboard = build_list_keyboard(items)
    rows = keyboard.inline_keyboard

    assert [button.text for button in rows[0]] == ["Milk · Куплено", "Удалить"]
    assert [button.callback_data for button in rows[0]] == ["done:1", "delete:1"]
    assert [button.text for button in rows[1]] == ["Bread · Вернуть", "Удалить"]
    assert [button.callback_data for button in rows[1]] == ["return:2", "delete:2"]
    assert [button.text for button in rows[2]] == ["Очистить купленное"]
    assert [button.callback_data for button in rows[2]] == ["clear_done"]


def test_build_list_keyboard_truncates_long_labels_before_action_text():
    item = GroceryItem(
        item_id=1,
        group_id=1,
        text="молоко Простоквашино и еще",
        created_by_user_id=1,
    )

    keyboard = build_list_keyboard([item])
    rows = keyboard.inline_keyboard

    assert len(rows) == 1
    assert [button.text for button in rows[0]] == ["молоко Простоква… · Куплено", "Удалить"]
    assert [button.callback_data for button in rows[0]] == ["done:1", "delete:1"]
