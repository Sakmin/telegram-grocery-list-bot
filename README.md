# Grocery Bot

Grocery Bot is the MVP for a shared grocery list bot. The core storage, service, rendering, and handler logic are implemented, but Telegram SDK transport wiring is still deferred in this environment because `python-telegram-bot` is not installed.

Today, `grocery_bot.main.build_application()` returns a local application object that assembles config, SQLite storage, the grocery list service, and registered handler callables. Building the application also initializes the database so the project is ready for a later Telegram adapter.

## Create a Telegram bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather).
2. Run `/newbot` and follow the prompts.
3. Copy the bot token BotFather gives you.

## Environment variables

- `BOT_TOKEN`: your Telegram bot token. The current local app object stores this in config but does not connect to Telegram yet.
- `DATABASE_PATH`: optional SQLite path. Defaults to `./data/grocery_bot.sqlite3` when `BOT_TOKEN` is configured.

If you build the app without `BOT_TOKEN`, it falls back to a local placeholder token and an in-memory SQLite database so tests and local smoke runs can still assemble the application object.

## Install

If you want an installed console script in a normal Python environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install setuptools wheel pytest
.venv/bin/pip install -e .
```

This workspace can also run the bot locally without installation by using `PYTHONPATH=src`.

## Run

Set your environment and build the local app wiring directly from the source tree:

```bash
export BOT_TOKEN="123456:replace-me"
export DATABASE_PATH="./data/grocery_bot.sqlite3"
PYTHONPATH=src .venv/bin/python -m grocery_bot.main
```

If you installed the package, you can use the console script instead:

```bash
.venv/bin/grocery-bot
```

The command initializes the SQLite schema and prints a summary of the registered local handlers. It does not start Telegram polling in this environment.
