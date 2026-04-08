from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(slots=True)
class BotConfig:
    bot_token: str
    database_path: Path


def load_config() -> BotConfig:
    return BotConfig(
        bot_token=os.environ["BOT_TOKEN"],
        database_path=Path(os.getenv("DATABASE_PATH", "./data/grocery_bot.sqlite3")),
    )
