from dataclasses import dataclass
from types import SimpleNamespace

import pytest
from telegram.error import BadRequest
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

from grocery_bot.handlers import EditListMessage, HandlerResult
from grocery_bot.main import RuntimeApplication, build_application, main
from grocery_bot.service import GroceryListService
from grocery_bot.storage import SQLiteStorage
from grocery_bot.telegram_runtime import execute_handler_result


def test_build_application_registers_real_telegram_handlers(tmp_path, monkeypatch):
    database_path = tmp_path / "runtime.sqlite3"
    monkeypatch.setenv("BOT_TOKEN", "123456:TEST-TOKEN")
    monkeypatch.setenv("DATABASE_PATH", str(database_path))

    app = build_application()

    assert app.telegram_application is not None
    assert app.database_initialized is True
    handlers = app.telegram_application.handlers[0]
    assert len(handlers) == 4
    assert isinstance(handlers[0], CommandHandler)
    assert isinstance(handlers[1], CommandHandler)
    assert isinstance(handlers[2], MessageHandler)
    assert isinstance(handlers[3], CallbackQueryHandler)


def test_main_skips_polling_in_validate_only_mode(monkeypatch, capsys, tmp_path):
    fake_telegram_application = FakeTelegramApplication()
    fake_runtime_application = RuntimeApplication(
        config=SimpleNamespace(bot_token="test-token", database_path=tmp_path / "runtime.sqlite3"),
        storage=SimpleNamespace(),
        service=SimpleNamespace(),
        telegram_application=fake_telegram_application,
        handlers=(),
        database_initialized=True,
    )

    monkeypatch.setenv("GROCERY_BOT_VALIDATE_ONLY", "1")
    monkeypatch.setattr("grocery_bot.main.build_application", lambda: fake_runtime_application)

    assert main() == 0
    assert fake_telegram_application.run_polling_calls == 0
    assert "Validate-only mode" in capsys.readouterr().out


@pytest.mark.anyio
async def test_execute_handler_result_recovers_from_missing_message(tmp_path):
    storage = SQLiteStorage(tmp_path / "runtime.sqlite3")
    storage.initialize()
    service = GroceryListService(storage)
    item = service.add_item(group_id=10, text="Milk", created_by_user_id=7)
    service.save_list_message(
        group_id=10,
        message_chat_id=10,
        message_id=99,
        is_pinned=True,
    )
    service.mark_done(group_id=10, item_id=item.item_id, actor_user_id=7)

    bot = FakeBot(missing_message_ids={99}, new_message_id=111)
    result = HandlerResult(
        actions=[
            EditListMessage(
                chat_id=10,
                message_id=99,
                text="Список покупок\nПока ничего не добавлено.\n\nКуплено:",
                reply_markup=[
                    [(f"Milk · Вернуть", f"return:{item.item_id}"), ("Удалить", f"delete:{item.item_id}")],
                    [("Очистить купленное", "clear_done")],
                ],
            )
        ]
    )

    await execute_handler_result(bot=bot, service=service, group_id=10, result=result)

    assert bot.sent_texts == ["Сообщение со списком было удалено, поэтому я отправил новое."]
    assert len(bot.posted_messages) == 1
    assert bot.posted_messages[0].text == "Список покупок\nПока ничего не добавлено.\n\nКуплено:"
    assert [[button.text for button in row] for row in bot.posted_messages[0].reply_markup.inline_keyboard] == [
        [f"Milk · Вернуть", "Удалить"],
        ["Очистить купленное"],
    ]
    assert [[button.callback_data for button in row] for row in bot.posted_messages[0].reply_markup.inline_keyboard] == [
        [f"return:{item.item_id}", f"delete:{item.item_id}"],
        ["clear_done"],
    ]
    snapshot = service.get_snapshot(group_id=10)
    assert snapshot.group.list_message_id == 111
    assert snapshot.group.list_message_chat_id == 10
    assert snapshot.group.is_pinned is True


@dataclass
class FakePostedMessage:
    chat_id: int
    text: str
    reply_markup: object
    message_id: int


class FakeBot:
    def __init__(self, missing_message_ids: set[int], new_message_id: int):
        self.missing_message_ids = missing_message_ids
        self.new_message_id = new_message_id
        self.sent_texts: list[str] = []
        self.posted_messages: list[FakePostedMessage] = []
        self.pinned_messages: list[tuple[int, int]] = []

    async def send_message(self, chat_id: int, text: str, reply_markup=None):
        if reply_markup is None:
            self.sent_texts.append(text)
            return SimpleNamespace(message_id=None)

        posted = FakePostedMessage(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            message_id=self.new_message_id,
        )
        self.posted_messages.append(posted)
        return SimpleNamespace(message_id=self.new_message_id)

    async def edit_message_text(self, chat_id: int, message_id: int, text: str, reply_markup=None):
        if message_id in self.missing_message_ids:
            raise BadRequest("Message to edit not found")
        return SimpleNamespace(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup)

    async def pin_chat_message(self, chat_id: int, message_id: int, disable_notification: bool = True):
        self.pinned_messages.append((chat_id, message_id))


class FakeTelegramApplication:
    def __init__(self):
        self.run_polling_calls = 0

    def run_polling(self):
        self.run_polling_calls += 1
