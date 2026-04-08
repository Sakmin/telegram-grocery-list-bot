# Grocery Bot

Grocery Bot is a Telegram bot for a shared grocery list in a group chat. The project now includes real runtime wiring with `python-telegram-bot`, SQLite persistence, the grocery list service layer, and recovery logic for stale inline actions and deleted list messages.

`grocery_bot.main.build_application()` assembles config, SQLite storage, the grocery list service, a real `python-telegram-bot` `Application`, and the registered Telegram handlers. Building the application initializes the database before polling starts.

## Create a Telegram bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather).
2. Run `/newbot` and follow the prompts.
3. Copy the bot token BotFather gives you.

## Environment variables

- `BOT_TOKEN`: your Telegram bot token. The current local app object stores this in config but does not connect to Telegram yet.
- `GROCERY_BOT_VALIDATE_ONLY`: optional flag for a startup-only verification run. Set to `1` to initialize the app and exit before polling.
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

The command initializes the SQLite schema, registers the Telegram handlers, and starts polling.

If you only want to verify startup wiring without opening a polling loop:

```bash
export GROCERY_BOT_VALIDATE_ONLY=1
PYTHONPATH=src .venv/bin/python -m grocery_bot.main
```
