# Grocery Bot Compact Action Buttons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update grocery item button labels so the main action uses emoji suffixes and the delete button is reduced to a compact `❌`, freeing more width for the item name.

**Architecture:** Keep the change entirely inside the existing rendering boundary. The production change is limited to button-label formatting in `src/grocery_bot/rendering.py`, and the test change updates rendering expectations to lock in the new emoji-based labels. No callback payloads, handler flow, or message-body copy change.

**Tech Stack:** Python 3.12, pytest, existing rendering module and rendering-focused tests

---

## File Map

- Modify: `src/grocery_bot/rendering.py`
  - Replace text action suffixes with emoji action suffixes.
  - Replace the delete button label with `❌`.
- Modify: `tests/test_rendering.py`
  - Update keyboard expectations to the new emoji labels.
  - Keep coverage for truncation and clear-done visibility.
- Modify: `tests/test_handlers.py`
  - Update handler-facing keyboard expectations to the new emoji labels.
- Modify: `tests/test_telegram_runtime.py`
  - Update runtime-facing keyboard expectations to the new emoji labels.

### Task 1: Lock Down Compact Emoji Button Labels

**Files:**
- Modify: `tests/test_rendering.py`
- Modify: `tests/test_handlers.py`
- Modify: `tests/test_telegram_runtime.py`
- Test: `tests/test_rendering.py`
- Test: `tests/test_handlers.py`
- Test: `tests/test_telegram_runtime.py`

- [ ] **Step 1: Write the failing rendering expectations**

Update the keyboard assertions so they expect:

```python
assert [button.text for button in rows[0]] == ["Milk · ✅", "❌"]
assert [button.text for button in rows[1]] == ["Bread · 🔙", "❌"]
assert [button.text for button in rows[2]] == ["Очистить купленное"]
```

Also update long-label and no-done-item tests to expect the same emoji action labels.
Update the matching handler/runtime expectations so item rows now use `✅`, `🔙`, and `❌` there as well.

- [ ] **Step 2: Run the rendering tests to verify they fail**

Run: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_rendering.py tests/test_handlers.py tests/test_telegram_runtime.py -v`
Expected: FAIL because the renderer and dependent expectations still use `Куплено`, `Вернуть`, and `Удалить`.

- [ ] **Step 3: Commit the red tests**

```bash
git add /Users/sergeysakmin/Desktop/Vs\ Code/Grocery\ list/tests/test_rendering.py /Users/sergeysakmin/Desktop/Vs\ Code/Grocery\ list/tests/test_handlers.py /Users/sergeysakmin/Desktop/Vs\ Code/Grocery\ list/tests/test_telegram_runtime.py
git commit -m "test: define compact emoji action labels"
```

### Task 2: Implement Compact Emoji Button Labels

**Files:**
- Modify: `src/grocery_bot/rendering.py`
- Test: `tests/test_rendering.py`
- Test: `tests/test_handlers.py`
- Test: `tests/test_telegram_runtime.py`

- [ ] **Step 1: Implement the minimal label change**

Update `_build_item_row()` so it renders:

```python
InlineKeyboardButton(text=f"{label} · ✅", callback_data=f"done:{item.item_id}")
InlineKeyboardButton(text=f"{label} · 🔙", callback_data=f"return:{item.item_id}")
InlineKeyboardButton(text="❌", callback_data=f"delete:{item.item_id}")
```

Leave `Очистить купленное` unchanged and do not modify callback payloads or truncation behavior.

- [ ] **Step 2: Run the affected tests to verify they pass**

Run: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_rendering.py tests/test_handlers.py tests/test_telegram_runtime.py -v`
Expected: PASS

- [ ] **Step 3: Commit the implementation**

```bash
git add /Users/sergeysakmin/Desktop/Vs\ Code/Grocery\ list/src/grocery_bot/rendering.py /Users/sergeysakmin/Desktop/Vs\ Code/Grocery\ list/tests/test_rendering.py /Users/sergeysakmin/Desktop/Vs\ Code/Grocery\ list/tests/test_handlers.py /Users/sergeysakmin/Desktop/Vs\ Code/Grocery\ list/tests/test_telegram_runtime.py
git commit -m "feat: compact grocery item action buttons"
```

### Task 3: Full Verification

**Files:**
- Modify: none expected
- Test: `tests/test_rendering.py`
- Test: `tests/test_handlers.py`
- Test: `tests/test_telegram_runtime.py`

- [ ] **Step 1: Run the focused affected test slice**

Run: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_rendering.py tests/test_handlers.py tests/test_telegram_runtime.py -v`
Expected: PASS

- [ ] **Step 2: Run the full suite**

Run: `PYTHONPATH=src .venv/bin/python -m pytest -v`
Expected: PASS

- [ ] **Step 3: Run validate-only startup**

Run: `BOT_TOKEN=test-token DATABASE_PATH=/tmp/grocery-bot-compact-buttons.sqlite3 GROCERY_BOT_VALIDATE_ONLY=1 PYTHONPATH=src .venv/bin/python -m grocery_bot.main`
Expected:
- prints `Grocery bot application assembled.`
- prints `Registered handlers: start, list, message, callback`
- exits successfully without polling

- [ ] **Step 4: Commit verification-ready state if needed**

```bash
git add /Users/sergeysakmin/Desktop/Vs\ Code/Grocery\ list/src/grocery_bot/rendering.py /Users/sergeysakmin/Desktop/Vs\ Code/Grocery\ list/tests/test_rendering.py
git commit -m "feat: finalize compact grocery action buttons"
```

Only create this commit if verification required an additional fix beyond Task 2.
