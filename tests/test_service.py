import pytest

from grocery_bot.service import (
    GroceryListService,
    InvalidItemOperationError,
    ItemNotFoundError,
)
from grocery_bot.storage import SQLiteStorage


def test_service_marks_item_done_and_returns_it(tmp_path):
    storage = SQLiteStorage(tmp_path / "bot.sqlite3")
    storage.initialize()
    service = GroceryListService(storage)

    item = service.add_item(group_id=1, text="Milk", created_by_user_id=10)
    service.mark_done(group_id=1, item_id=item.item_id, actor_user_id=10)
    updated = service.return_item(group_id=1, item_id=item.item_id)

    assert updated.status.value == "active"


def test_service_duplicate_hints_only_include_active_items(tmp_path):
    storage = SQLiteStorage(tmp_path / "bot.sqlite3")
    storage.initialize()
    service = GroceryListService(storage)

    active = service.add_item(group_id=1, text="Milk", created_by_user_id=10)
    done = service.add_item(group_id=1, text="Bread", created_by_user_id=10)
    service.mark_done(group_id=1, item_id=done.item_id, actor_user_id=10)

    hints = service.find_duplicate_hints(group_id=1, text=" milk ")

    assert hints == [active]


def test_service_raises_for_missing_or_invalid_item_operations(tmp_path):
    storage = SQLiteStorage(tmp_path / "bot.sqlite3")
    storage.initialize()
    service = GroceryListService(storage)

    with pytest.raises(ItemNotFoundError):
        service.mark_done(group_id=1, item_id=999, actor_user_id=10)

    item = service.add_item(group_id=1, text="Milk", created_by_user_id=10)

    with pytest.raises(InvalidItemOperationError):
        service.return_item(group_id=1, item_id=item.item_id)


def test_service_returns_current_list_snapshot(tmp_path):
    storage = SQLiteStorage(tmp_path / "bot.sqlite3")
    storage.initialize()
    service = GroceryListService(storage)

    item = service.add_item(group_id=22, text="Milk", created_by_user_id=10)
    snapshot = service.get_snapshot(group_id=22)

    assert snapshot.group.group_id == 22
    assert snapshot.items == [item]


def test_service_saves_and_clears_list_message_metadata(tmp_path):
    storage = SQLiteStorage(tmp_path / "bot.sqlite3")
    storage.initialize()
    service = GroceryListService(storage)

    saved = service.save_list_message(
        group_id=22,
        message_chat_id=22,
        message_id=101,
        is_pinned=True,
    )

    assert saved.list_message_id == 101
    assert saved.list_message_chat_id == 22
    assert saved.is_pinned is True

    unchanged = service.clear_list_message(group_id=22, expected_message_id=999)
    assert unchanged.list_message_id == 101
    assert unchanged.list_message_chat_id == 22
    assert unchanged.is_pinned is True

    cleared = service.clear_list_message(group_id=22, expected_message_id=101)
    assert cleared.list_message_id is None
    assert cleared.list_message_chat_id is None
    assert cleared.is_pinned is False
