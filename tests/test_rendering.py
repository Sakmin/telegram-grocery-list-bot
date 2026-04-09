from grocery_bot.models import GroceryItem, GroceryItemStatus
from grocery_bot.rendering import build_list_keyboard, render_list_text


DONE_ITEM = GroceryItem(
    item_id=2,
    group_id=1,
    text="Bread",
    created_by_user_id=1,
    status=GroceryItemStatus.DONE,
)
ACTIVE_ITEM = GroceryItem(item_id=1, group_id=1, text="Milk", created_by_user_id=1)


def test_render_list_text_shows_short_empty_state():
    assert render_list_text([]) == "Список покупок\nПока ничего не добавлено."


def test_render_list_text_shows_short_bought_section_when_only_done_items():
    assert render_list_text([DONE_ITEM]) == "Список покупок\nПока ничего не добавлено.\n\nКуплено:"


def test_render_list_text_hides_item_names_in_mixed_state():
    assert render_list_text([ACTIVE_ITEM, DONE_ITEM]) == "Список покупок\n\nКуплено:"


def test_render_list_text_hides_item_names_in_active_only_state():
    assert render_list_text([ACTIVE_ITEM]) == "Список покупок"


def test_build_list_keyboard_puts_item_label_in_first_button_and_adds_clear_row():
    keyboard = build_list_keyboard([ACTIVE_ITEM, DONE_ITEM])
    rows = keyboard.inline_keyboard

    assert [button.text for button in rows[0]] == ["Milk · ✅", "❌"]
    assert [button.callback_data for button in rows[0]] == ["done:1", "delete:1"]
    assert [button.text for button in rows[1]] == ["Bread · 🔙", "❌"]
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
    assert [button.text for button in rows[0]] == ["молоко Простокваш… · ✅", "❌"]
    assert [button.callback_data for button in rows[0]] == ["done:1", "delete:1"]


def test_build_list_keyboard_omits_clear_bought_when_no_done_items():
    keyboard = build_list_keyboard([ACTIVE_ITEM])
    rows = keyboard.inline_keyboard

    assert len(rows) == 1
    assert [button.text for button in rows[0]] == ["Milk · ✅", "❌"]
    assert [button.callback_data for button in rows[0]] == ["done:1", "delete:1"]


def test_build_list_keyboard_truncates_labels_at_the_18_character_boundary():
    keyboard = build_list_keyboard(
        [
            GroceryItem(
                item_id=3,
                group_id=1,
                text="123456789012345678",
                created_by_user_id=1,
            ),
            GroceryItem(
                item_id=4,
                group_id=1,
                text="1234567890123456789",
                created_by_user_id=1,
            ),
        ]
    )

    rows = keyboard.inline_keyboard

    assert [button.text for button in rows[0]] == ["123456789012345678 · ✅", "❌"]
    assert [button.text for button in rows[1]] == ["12345678901234567… · ✅", "❌"]
