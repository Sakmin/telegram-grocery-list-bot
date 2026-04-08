from dataclasses import dataclass
from pathlib import Path
import os

from telegram.ext import Application, ApplicationBuilder

from grocery_bot.config import BotConfig, load_config
from grocery_bot.service import GroceryListService
from grocery_bot.storage import SQLiteStorage
from grocery_bot.telegram_runtime import (
    TelegramHandlerRegistration,
    build_telegram_handlers,
    register_telegram_handlers,
)
DEFAULT_LOCAL_BOT_TOKEN = "local-development-token"
VALIDATE_ONLY_ENV = "GROCERY_BOT_VALIDATE_ONLY"


@dataclass(slots=True, frozen=True)
class RuntimeApplication:
    config: BotConfig
    storage: SQLiteStorage
    service: GroceryListService
    telegram_application: Application
    handlers: tuple[TelegramHandlerRegistration, ...]
    database_initialized: bool


def build_application() -> RuntimeApplication:
    config = _load_application_config()
    storage = SQLiteStorage(config.database_path)
    storage.initialize()
    service = GroceryListService(storage)
    telegram_application = ApplicationBuilder().token(config.bot_token).build()
    handlers = build_telegram_handlers(service)
    register_telegram_handlers(telegram_application, handlers)
    return RuntimeApplication(
        config=config,
        storage=storage,
        service=service,
        telegram_application=telegram_application,
        handlers=handlers,
        database_initialized=True,
    )


def main() -> int:
    application = build_application()
    route_names = ", ".join(handler.name for handler in application.handlers)

    print("Grocery bot application assembled.")
    print(f"Database initialized: {application.database_initialized}")
    print(f"Database path: {application.config.database_path}")
    print(f"Registered handlers: {route_names}")
    if os.getenv(VALIDATE_ONLY_ENV) == "1":
        print("Validate-only mode enabled. Skipping Telegram polling.")
        return 0
    print("Starting Telegram polling.")
    application.telegram_application.run_polling()
    return 0


def _load_application_config() -> BotConfig:
    try:
        return load_config()
    except KeyError:
        return BotConfig(
            bot_token=os.getenv("BOT_TOKEN", DEFAULT_LOCAL_BOT_TOKEN),
            database_path=Path(os.getenv("DATABASE_PATH", ":memory:")),
        )


if __name__ == "__main__":
    raise SystemExit(main())
