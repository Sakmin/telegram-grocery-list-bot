from grocery_bot.main import build_application
from grocery_bot.handlers import (
    AnswerCallback,
    CallbackAction,
    EditListMessage,
    HandlerRequest,
    PostListMessage,
    SendTextMessage,
    extract_add_text,
    handle_callback,
    handle_list,
    handle_message,
    handle_start,
    parse_callback_data,
    refresh_list_message,
)
from grocery_bot.models import GroceryItem, GroceryItemStatus, GroupList
from grocery_bot.service import (
    GroceryListService,
    GroceryListSnapshot,
    ItemNotFoundError,
)
from grocery_bot.storage import SQLiteStorage
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler


def test_build_application_returns_application_instance(tmp_path, monkeypatch):
    database_path = tmp_path / "smoke.sqlite3"
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("DATABASE_PATH", str(database_path))

    app = build_application()

    assert app is not None
    assert app.config.bot_token == "test-token"
    assert app.config.database_path == database_path
    assert app.database_initialized is True
    assert database_path.exists()
    assert [handler.name for handler in app.handlers] == [
        "start",
        "list",
        "message",
        "callback",
    ]
    assert [type(handler.handler) for handler in app.handlers] == [
        CommandHandler,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
    ]
    assert app.service.get_snapshot(group_id=10).group.group_id == 10


def test_extract_add_text_from_plus_prefix():
    assert extract_add_text("+ milk") == "milk"


def test_extract_add_text_from_add_command():
    assert extract_add_text("/add milk") == "milk"


def test_handle_message_rejects_non_group_chat(tmp_path):
    service = build_service(tmp_path)

    result = handle_message(
        service=service,
        request=HandlerRequest(
            chat_id=50,
            user_id=7,
            chat_type="private",
            text="+ milk",
        ),
    )

    assert result.actions == [
        SendTextMessage(chat_id=50, text="Этот бот работает только в группах.")
    ]


def test_parse_callback_data_variants():
    assert parse_callback_data("done:1") == CallbackAction(name="done", item_id=1)
    assert parse_callback_data("return:2") == CallbackAction(name="return", item_id=2)
    assert parse_callback_data("delete:3") == CallbackAction(name="delete", item_id=3)
    assert parse_callback_data("clear_done") == CallbackAction(name="clear_done", item_id=None)


def test_handle_start_posts_list_when_missing(tmp_path):
    service = FakeService(group=GroupList(group_id=10))

    result = handle_start(
        service=service,
        request=HandlerRequest(chat_id=10, user_id=7, chat_type="group"),
    )

    assert result.actions == [
        PostListMessage(
            chat_id=10,
            text="Список покупок\nПока ничего не добавлено.",
            reply_markup=[],
        )
    ]


def test_handle_list_edits_existing_list_message(tmp_path):
    service = FakeService(
        group=GroupList(
            group_id=10,
            list_message_id=99,
            list_message_chat_id=10,
            is_pinned=True,
        )
    )

    result = handle_list(
        service=service,
        request=HandlerRequest(chat_id=10, user_id=7, chat_type="group"),
    )

    assert result.actions == [
        EditListMessage(
            chat_id=10,
            message_id=99,
            text="Список покупок\nПока ничего не добавлено.",
            reply_markup=[],
        )
    ]


def test_handle_callback_marks_item_done_and_refreshes_list(tmp_path):
    item = GroceryItem(item_id=1, group_id=10, text="Milk", created_by_user_id=7)
    bread = GroceryItem(item_id=2, group_id=10, text="Bread", created_by_user_id=7)
    service = FakeService(
        group=GroupList(
            group_id=10,
            list_message_id=99,
            list_message_chat_id=10,
            is_pinned=True,
        ),
        items=[item, bread],
    )

    result = handle_callback(
        service=service,
        request=HandlerRequest(
            chat_id=10,
            user_id=7,
            chat_type="group",
            callback_data=f"done:{item.item_id}",
        ),
    )

    assert result.actions == [
        EditListMessage(
            chat_id=10,
            message_id=99,
            text="Список покупок\n\nКуплено:",
            reply_markup=[
                [(f"Milk · 🔙", f"return:{item.item_id}"), ("❌", f"delete:{item.item_id}")],
                [(f"Bread · ✅", f"done:{bread.item_id}"), ("❌", f"delete:{bread.item_id}")],
                [("Очистить купленное", "clear_done")],
            ],
        )
    ]


def test_handle_callback_can_return_delete_and_clear_done_items(tmp_path):
    milk = GroceryItem(item_id=1, group_id=10, text="Milk", created_by_user_id=7)
    bread = GroceryItem(
        item_id=2,
        group_id=10,
        text="Bread",
        created_by_user_id=7,
        status=GroceryItemStatus.DONE,
    )
    service = FakeService(
        group=GroupList(
            group_id=10,
            list_message_id=99,
            list_message_chat_id=10,
            is_pinned=True,
        ),
        items=[milk, bread],
    )

    returned = handle_callback(
        service=service,
        request=HandlerRequest(
            chat_id=10,
            user_id=7,
            chat_type="group",
            callback_data=f"return:{bread.item_id}",
        ),
    )
    deleted = handle_callback(
        service=service,
        request=HandlerRequest(
            chat_id=10,
            user_id=7,
            chat_type="group",
            callback_data=f"delete:{milk.item_id}",
        ),
    )
    cleared = handle_callback(
        service=service,
        request=HandlerRequest(
            chat_id=10,
            user_id=7,
            chat_type="group",
            callback_data="clear_done",
        ),
    )

    assert returned.actions == [
        EditListMessage(
            chat_id=10,
            message_id=99,
            text="Список покупок",
            reply_markup=[
                [(f"Milk · ✅", f"done:{milk.item_id}"), ("❌", f"delete:{milk.item_id}")],
                [(f"Bread · ✅", f"done:{bread.item_id}"), ("❌", f"delete:{bread.item_id}")],
            ],
        )
    ]
    assert deleted.actions == [
        EditListMessage(
            chat_id=10,
            message_id=99,
            text="Список покупок",
            reply_markup=[
                [(f"Bread · ✅", f"done:{bread.item_id}"), ("❌", f"delete:{bread.item_id}")],
            ],
        )
    ]
    assert cleared.actions == [
        EditListMessage(
            chat_id=10,
            message_id=99,
            text="Список покупок",
            reply_markup=[
                [(f"Bread · ✅", f"done:{bread.item_id}"), ("❌", f"delete:{bread.item_id}")],
            ],
        )
    ]


def test_refresh_list_message_recovers_when_saved_message_is_missing(tmp_path):
    service = build_service(tmp_path)
    item = service.add_item(group_id=10, text="Milk", created_by_user_id=7)
    service.save_list_message(
        group_id=10,
        message_chat_id=10,
        message_id=99,
        is_pinned=True,
    )

    result = refresh_list_message(
        service=service,
        group_id=10,
        missing_message_id=99,
    )

    assert result.actions == [
        SendTextMessage(
            chat_id=10,
            text="Сообщение со списком было удалено, поэтому я отправил новое.",
        ),
        PostListMessage(
            chat_id=10,
            text="Список покупок",
            reply_markup=[
                [(f"Milk · ✅", f"done:{item.item_id}"), ("❌", f"delete:{item.item_id}")],
            ],
        ),
    ]
    snapshot = service.get_snapshot(group_id=10)
    assert snapshot.group.list_message_id is None
    assert snapshot.group.list_message_chat_id is None
    assert snapshot.group.is_pinned is False


def test_handle_callback_repeated_done_is_idempotent(tmp_path):
    service = build_service(tmp_path)
    item = service.add_item(group_id=10, text="Milk", created_by_user_id=7)
    bread = service.add_item(group_id=10, text="Bread", created_by_user_id=7)
    service.save_list_message(
        group_id=10,
        message_chat_id=10,
        message_id=99,
        is_pinned=True,
    )

    first_result = handle_callback(
        service=service,
        request=HandlerRequest(
            chat_id=10,
            user_id=7,
            chat_type="group",
            callback_data=f"done:{item.item_id}",
        ),
    )
    second_result = handle_callback(
        service=service,
        request=HandlerRequest(
            chat_id=10,
            user_id=7,
            chat_type="group",
            callback_data=f"done:{item.item_id}",
        ),
    )

    assert first_result.actions == [
        EditListMessage(
            chat_id=10,
            message_id=99,
            text="Список покупок\n\nКуплено:",
            reply_markup=[
                [(f"Milk · 🔙", f"return:{item.item_id}"), ("❌", f"delete:{item.item_id}")],
                [(f"Bread · ✅", f"done:{bread.item_id}"), ("❌", f"delete:{bread.item_id}")],
                [("Очистить купленное", "clear_done")],
            ],
        )
    ]
    assert second_result.actions == [
        AnswerCallback(text="Это действие больше не доступно.")
    ]


def test_handle_callback_recovers_when_saved_message_is_missing(tmp_path):
    service = build_service(tmp_path)
    item = service.add_item(group_id=10, text="Milk", created_by_user_id=7)
    bread = service.add_item(group_id=10, text="Bread", created_by_user_id=7)
    service.save_list_message(
        group_id=10,
        message_chat_id=10,
        message_id=99,
        is_pinned=True,
    )

    result = handle_callback(
        service=service,
        request=HandlerRequest(
            chat_id=10,
            user_id=7,
            chat_type="group",
            callback_data=f"done:{item.item_id}",
            missing_message_id=99,
        ),
    )

    assert result.actions == [
        SendTextMessage(
            chat_id=10,
            text="Сообщение со списком было удалено, поэтому я отправил новое.",
        ),
        PostListMessage(
            chat_id=10,
            text="Список покупок\n\nКуплено:",
            reply_markup=[
                [(f"Milk · 🔙", f"return:{item.item_id}"), ("❌", f"delete:{item.item_id}")],
                [(f"Bread · ✅", f"done:{bread.item_id}"), ("❌", f"delete:{bread.item_id}")],
                [("Очистить купленное", "clear_done")],
            ],
        ),
    ]
    snapshot = service.get_snapshot(group_id=10)
    assert snapshot.group.list_message_id is None
    assert snapshot.group.list_message_chat_id is None
    assert snapshot.group.is_pinned is False


def test_handle_callback_returns_benign_message_for_malformed_payload():
    service = FakeService(group=GroupList(group_id=10))

    result = handle_callback(
        service=service,
        request=HandlerRequest(
            chat_id=10,
            user_id=7,
            chat_type="group",
            callback_data="done:not-a-number",
        ),
    )

    assert result.actions == [
        AnswerCallback(text="Это действие больше не доступно.")
    ]


def test_handle_callback_returns_benign_message_for_stale_well_formed_payload():
    service = StaleItemService(group=GroupList(group_id=10))

    result = handle_callback(
        service=service,
        request=HandlerRequest(
            chat_id=10,
            user_id=7,
            chat_type="group",
            callback_data="done:1",
        ),
    )

    assert result.actions == [
        AnswerCallback(text="Это действие больше не доступно.")
    ]


def build_service(tmp_path):
    storage = SQLiteStorage(tmp_path / "bot.sqlite3")
    storage.initialize()
    return GroceryListService(storage)


class FakeService:
    def __init__(self, group: GroupList, items: list[GroceryItem] | None = None):
        self.group = group
        self.items = list(items or [])

    def get_snapshot(self, group_id: int) -> GroceryListSnapshot:
        assert group_id == self.group.group_id
        return GroceryListSnapshot(group=self.group, items=list(self.items))

    def mark_done(self, group_id: int, item_id: int, actor_user_id: int) -> GroceryItem:
        _ = actor_user_id
        return self._set_status(group_id=group_id, item_id=item_id, status=GroceryItemStatus.DONE)

    def return_item(self, group_id: int, item_id: int) -> GroceryItem:
        return self._set_status(group_id=group_id, item_id=item_id, status=GroceryItemStatus.ACTIVE)

    def delete_item(self, group_id: int, item_id: int) -> GroceryItem:
        assert group_id == self.group.group_id
        item = self._get_item(item_id=item_id)
        self.items = [existing for existing in self.items if existing.item_id != item_id]
        return item

    def clear_done_items(self, group_id: int) -> list[GroceryItem]:
        assert group_id == self.group.group_id
        done_items = [item for item in self.items if item.status is GroceryItemStatus.DONE]
        self.items = [item for item in self.items if item.status is not GroceryItemStatus.DONE]
        return done_items

    def _set_status(
        self,
        group_id: int,
        item_id: int,
        status: GroceryItemStatus,
    ) -> GroceryItem:
        assert group_id == self.group.group_id
        item = self._get_item(item_id=item_id)
        item.status = status
        return item

    def _get_item(self, item_id: int) -> GroceryItem:
        return next(item for item in self.items if item.item_id == item_id)


class StaleItemService(FakeService):
    def mark_done(self, group_id: int, item_id: int, actor_user_id: int) -> GroceryItem:
        _ = group_id
        _ = item_id
        _ = actor_user_id
        raise ItemNotFoundError("item 1 does not exist in group 10")
