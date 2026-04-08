import sqlite3

from grocery_bot.models import GroceryItemStatus
from grocery_bot.storage import SQLiteStorage


def test_storage_creates_group_and_item(tmp_path):
    database_path = tmp_path / "bot.sqlite3"
    storage = SQLiteStorage(database_path)
    storage.initialize()

    storage.ensure_group(group_id=123)
    item = storage.add_item(group_id=123, text="Milk", created_by_user_id=1)

    fresh_storage = SQLiteStorage(database_path)
    items = fresh_storage.list_items(group_id=123)
    assert [entry.text for entry in items] == ["Milk"]
    assert item.group_id == 123


def test_storage_updates_item_status_and_clears_done_items(tmp_path):
    database_path = tmp_path / "bot.sqlite3"
    storage = SQLiteStorage(database_path)
    storage.initialize()

    first = storage.add_item(group_id=123, text="Milk", created_by_user_id=1)
    storage.add_item(group_id=123, text="Bread", created_by_user_id=1)

    storage.update_item_status(group_id=123, item_id=first.item_id, status=GroceryItemStatus.DONE)

    fresh_storage = SQLiteStorage(database_path)
    items = fresh_storage.list_items(group_id=123)
    assert [entry.status for entry in items] == [GroceryItemStatus.DONE, GroceryItemStatus.ACTIVE]

    fresh_storage.clear_done_items(group_id=123)

    reloaded_storage = SQLiteStorage(database_path)
    remaining = reloaded_storage.list_items(group_id=123)
    assert [entry.text for entry in remaining] == ["Bread"]


def test_storage_deletes_item(tmp_path):
    database_path = tmp_path / "bot.sqlite3"
    storage = SQLiteStorage(database_path)
    storage.initialize()

    item = storage.add_item(group_id=123, text="Milk", created_by_user_id=1)

    fresh_storage = SQLiteStorage(database_path)
    fresh_storage.delete_item(group_id=123, item_id=item.item_id)

    reloaded_storage = SQLiteStorage(database_path)
    assert reloaded_storage.list_items(group_id=123) == []


def test_storage_persists_group_message_metadata(tmp_path):
    database_path = tmp_path / "bot.sqlite3"
    storage = SQLiteStorage(database_path)
    storage.initialize()

    storage.ensure_group(group_id=123)
    storage.update_group_message(
        group_id=123,
        list_message_id=77,
        list_message_chat_id=88,
        is_pinned=True,
    )

    fresh_storage = SQLiteStorage(database_path)
    group = fresh_storage.ensure_group(group_id=123)
    assert group.list_message_id == 77
    assert group.list_message_chat_id == 88
    assert group.is_pinned is True


def test_storage_enforces_foreign_keys_on_fresh_connection(tmp_path):
    database_path = tmp_path / "bot.sqlite3"
    storage = SQLiteStorage(database_path)
    storage.initialize()

    fresh_storage = SQLiteStorage(database_path)
    with fresh_storage._connect() as connection:
        try:
            connection.execute(
                """
                INSERT INTO items (group_id, text, created_by_user_id)
                VALUES (?, ?, ?)
                """,
                (999, "Milk", 1),
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("expected foreign key enforcement to reject missing group")
