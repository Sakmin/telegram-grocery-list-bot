# Grocery Bot Button-First List Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the duplicated text list layout with a button-first Telegram list where grocery items are rendered only as inline keyboard rows, while the message body stays short and Russian-first.

**Architecture:** Keep the change inside the existing rendering boundary. Update `render_list_text()` to produce only the short message header and bought-section label, and update `build_list_keyboard()` to carry compact item names in the action buttons. Adjust handler-facing tests to assert the new rendered message and keyboard payloads without touching storage or service behavior.

**Tech Stack:** Python 3.12, pytest, python-telegram-bot test doubles, existing rendering/handler modules

---

## File Map

- Modify: `src/grocery_bot/rendering.py`
  - Change message text generation to button-first layout.
  - Add deterministic label-shortening helper for button text.
  - Update keyboard building so each item row includes its compact item name plus action label.
- Modify: `tests/test_rendering.py`
  - Replace old text-list expectations with button-first message expectations.
  - Add truncation coverage for long item labels.
- Modify: `tests/test_handlers.py`
  - Update handler expectations so edited/posted list messages reflect the new text body and keyboard labels.
- Modify: `tests/test_telegram_runtime.py`
  - Update runtime recovery expectations so reposted list messages and keyboard rows match the new button-first UI.

### Task 1: Lock Down Button-First Rendering Expectations

**Files:**
- Modify: `tests/test_rendering.py`
- Test: `tests/test_rendering.py`

- [ ] **Step 1: Write the failing rendering expectations**

Add or update tests so they assert:

```python
assert render_list_text([]) == "Список покупок\nПока ничего не добавлено."

assert render_list_text([
    GroceryItem(item_id=2, group_id=1, text="Bread", created_by_user_id=1, status=GroceryItemStatus.DONE),
]) == "Список покупок\nПока ничего не добавлено.\n\nКуплено:"
```

And for keyboard rows:

```python
assert [button.text for button in rows[0]] == ["Milk · Куплено", "Удалить"]
assert [button.text for button in rows[1]] == ["Bread · Вернуть", "Удалить"]
assert [button.text for button in rows[2]] == ["Очистить купленное"]
```

- [ ] **Step 2: Run rendering tests to verify they fail**

Run: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_rendering.py -v`
Expected: FAIL because the current renderer still outputs the old text list and short action-only buttons.

- [ ] **Step 3: Add truncation test coverage**

Add a focused test like:

```python
item = GroceryItem(
    item_id=1,
    group_id=1,
    text="молоко Простоквашино 1 литр",
    created_by_user_id=1,
)

keyboard = build_list_keyboard([item])
assert keyboard.inline_keyboard[0][0].text == "молоко Простоква… · Куплено"
```

- [ ] **Step 4: Run rendering tests again**

Run: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_rendering.py -v`
Expected: FAIL, now explicitly covering both layout and truncation gaps.

- [ ] **Step 5: Commit the red tests**

```bash
git add /Users/sergeysakmin/Desktop/Vs\ Code/Grocery\ list/tests/test_rendering.py
git commit -m "test: define button-first grocery list rendering"
```

### Task 2: Implement Button-First Rendering

**Files:**
- Modify: `src/grocery_bot/rendering.py`
- Test: `tests/test_rendering.py`

- [ ] **Step 1: Implement the minimal rendering changes**

Update `render_list_text()` to:
- always start with `Список покупок`
- render `Пока ничего не добавлено.` when there are no active items
- add `Куплено:` only when at least one bought item exists
- never render active or bought items as plain text lines

Update `build_list_keyboard()` to:
- keep the existing item iteration order from the snapshot, while rendering active and bought rows in the same order they are already provided by the service
- render button labels as `<short item label> · Куплено` or `<short item label> · Вернуть`
- keep `Удалить` as the second button
- keep `Очистить купленное` as the last row only when bought items exist

Add a small helper with the exact truncation rule:

```python
def shorten_item_label(text: str) -> str:
    if len(text) <= 18:
        return text
    return f"{text[:17]}…"
```

- [ ] **Step 2: Run rendering tests to verify they pass**

Run: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_rendering.py -v`
Expected: PASS

- [ ] **Step 3: Commit the rendering implementation**

```bash
git add /Users/sergeysakmin/Desktop/Vs\ Code/Grocery\ list/src/grocery_bot/rendering.py /Users/sergeysakmin/Desktop/Vs\ Code/Grocery\ list/tests/test_rendering.py
git commit -m "feat: switch grocery list to button-first rendering"
```

### Task 3: Align Handler Expectations With The New UI

**Files:**
- Modify: `tests/test_handlers.py`
- Modify: `tests/test_telegram_runtime.py`
- Test: `tests/test_handlers.py`
- Test: `tests/test_telegram_runtime.py`

- [ ] **Step 1: Update handler tests to the new rendered output**

Adjust expectations so examples look like:

```python
PostListMessage(
    chat_id=10,
    text="Список покупок\nПока ничего не добавлено.",
    reply_markup=[],
)
```

And callback refresh assertions use button text with item names, for example:

```python
reply_markup=[
    [("Milk · Вернуть", "return:1"), ("Удалить", "delete:1")],
    [("Очистить купленное", "clear_done")],
]
```

For mixed states, assert the message body contains `Куплено:` when done items exist, but no text-rendered item lines.

Update runtime recovery expectations in `tests/test_telegram_runtime.py` to match the same message body and named buttons after reposting a missing pinned message.

- [ ] **Step 2: Run handler tests to verify they fail**

Run: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_handlers.py tests/test_telegram_runtime.py -v`
Expected: FAIL until the handler-facing rendering output matches the new UI contract.

- [ ] **Step 3: Re-run handler and runtime tests after rendering changes**

Run: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_handlers.py tests/test_telegram_runtime.py -v`
Expected: PASS once the rendering module output already satisfies the new expectations.

- [ ] **Step 4: Commit the handler expectation updates**

```bash
git add /Users/sergeysakmin/Desktop/Vs\ Code/Grocery\ list/tests/test_handlers.py /Users/sergeysakmin/Desktop/Vs\ Code/Grocery\ list/tests/test_telegram_runtime.py
git commit -m "test: align handlers with button-first grocery ui"
```

### Task 4: Full Verification

**Files:**
- Modify: none expected
- Test: `tests/test_rendering.py`
- Test: `tests/test_handlers.py`
- Test: `tests/test_telegram_runtime.py`

- [ ] **Step 1: Run the focused bot test suite**

Run: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_rendering.py tests/test_handlers.py tests/test_telegram_runtime.py -v`
Expected: PASS

- [ ] **Step 2: Run the full project test suite**

Run: `PYTHONPATH=src .venv/bin/python -m pytest -v`
Expected: PASS

- [ ] **Step 3: Run startup validation**

Run: `BOT_TOKEN=test-token DATABASE_PATH=/tmp/grocery-bot-button-list.sqlite3 GROCERY_BOT_VALIDATE_ONLY=1 PYTHONPATH=src .venv/bin/python -m grocery_bot.main`
Expected:
- prints `Grocery bot application assembled.`
- prints `Registered handlers: start, list, message, callback`
- exits successfully without polling

- [ ] **Step 4: Commit verification-ready state**

```bash
git add /Users/sergeysakmin/Desktop/Vs\ Code/Grocery\ list/src/grocery_bot/rendering.py /Users/sergeysakmin/Desktop/Vs\ Code/Grocery\ list/tests/test_rendering.py /Users/sergeysakmin/Desktop/Vs\ Code/Grocery\ list/tests/test_handlers.py /Users/sergeysakmin/Desktop/Vs\ Code/Grocery\ list/tests/test_telegram_runtime.py
git commit -m "feat: finalize button-first grocery list ui"
```
