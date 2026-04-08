from grocery_bot.models import GroceryItem, GroceryItemStatus
from grocery_bot.rendering import build_list_keyboard, render_list_text


def test_render_list_text_separates_active_and_done_items():
    items = [
        GroceryItem(item_id=1, group_id=1, text="Milk", created_by_user_id=1),
        GroceryItem(
            item_id=2,
            group_id=1,
            text="Bread",
            created_by_user_id=1,
            status=GroceryItemStatus.DONE,
        ),
    ]

    assert render_list_text(items) == "Список покупок\nНужно купить\n- Milk\n\nКуплено\n- Bread"


def test_render_list_text_shows_empty_state_when_no_items():
    assert render_list_text([]) == "Список покупок\nНужно купить\n• Пока пусто.\n\nКуплено\n• Пока ничего не куплено."


def test_build_list_keyboard_exposes_item_and_global_actions():
    items = [
        GroceryItem(item_id=1, group_id=1, text="Milk", created_by_user_id=1),
        GroceryItem(
            item_id=2,
            group_id=1,
            text="Bread",
            created_by_user_id=1,
            status=GroceryItemStatus.DONE,
        ),
    ]

    keyboard = build_list_keyboard(items)
    rows = keyboard.inline_keyboard

    assert [button.text for button in rows[0]] == ["Куплено", "Удалить"]
    assert [button.callback_data for button in rows[0]] == ["done:1", "delete:1"]
    assert [button.text for button in rows[1]] == ["Вернуть", "Удалить"]
    assert [button.callback_data for button in rows[1]] == ["return:2", "delete:2"]
    assert [button.text for button in rows[2]] == ["Очистить купленное"]
    assert [button.callback_data for button in rows[2]] == ["clear_done"]


def test_build_list_keyboard_omits_clear_bought_when_no_done_items():
    items = [
        GroceryItem(item_id=1, group_id=1, text="Milk", created_by_user_id=1),
    ]

    keyboard = build_list_keyboard(items)
    rows = keyboard.inline_keyboard

    assert len(rows) == 1
    assert [button.text for button in rows[0]] == ["Куплено", "Удалить"]
    assert [button.callback_data for button in rows[0]] == ["done:1", "delete:1"]
