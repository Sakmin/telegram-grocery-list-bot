from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import os

from grocery_bot.config import BotConfig, load_config
from grocery_bot.handlers import (
    HandlerRequest,
    HandlerResult,
    handle_callback,
    handle_list,
    handle_message,
    handle_start,
)
from grocery_bot.service import GroceryListService
from grocery_bot.storage import SQLiteStorage

HandlerCallable = Callable[[GroceryListService, HandlerRequest], HandlerResult]
DEFAULT_LOCAL_BOT_TOKEN = "local-development-token"


@dataclass(slots=True, frozen=True)
class RegisteredHandler:
    name: str
    trigger: str
    callback: HandlerCallable


@dataclass(slots=True)
class LocalApplication:
    config: BotConfig
    storage: SQLiteStorage
    service: GroceryListService
    handlers: tuple[RegisteredHandler, ...]
    database_initialized: bool = False

    def initialize(self) -> None:
        self.storage.initialize()
        self.database_initialized = True


def build_application() -> LocalApplication:
    config = _load_application_config()
    storage = SQLiteStorage(config.database_path)
    service = GroceryListService(storage)
    application = LocalApplication(
        config=config,
        storage=storage,
        service=service,
        handlers=_build_handlers(),
    )
    application.initialize()
    return application


def main() -> int:
    application = build_application()
    route_names = ", ".join(handler.name for handler in application.handlers)

    print("Grocery bot application assembled.")
    print(f"Database initialized: {application.database_initialized}")
    print(f"Database path: {application.config.database_path}")
    print(f"Registered handlers: {route_names}")
    print("Telegram transport wiring is represented locally in this environment.")
    return 0


def _build_handlers() -> tuple[RegisteredHandler, ...]:
    return (
        RegisteredHandler(name="start", trigger="/start", callback=handle_start),
        RegisteredHandler(name="list", trigger="/list", callback=handle_list),
        RegisteredHandler(name="message", trigger="group text message", callback=handle_message),
        RegisteredHandler(name="callback", trigger="inline button callback", callback=handle_callback),
    )


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
