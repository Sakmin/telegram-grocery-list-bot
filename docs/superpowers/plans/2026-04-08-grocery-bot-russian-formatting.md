# Grocery Bot Russian Formatting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the grocery bot message formatting and button labels so the user-facing interface is fully in Russian and visually clearer in Telegram.

**Architecture:** Keep the change presentation-only. Update rendering text, inline button labels, and any handler/runtime tests that assert exact copy. Preserve existing business logic, action availability, and item lifecycle behavior.

**Tech Stack:** Python 3.12+, `python-telegram-bot`, `pytest`

---

## Proposed File Structure

- Modify: `src/grocery_bot/rendering.py`
  Responsibility: Russian list text and button labels.
- Modify: `src/grocery_bot/handlers.py`
  Responsibility: Russian recovery/stale/group-only copy if needed for consistency.
- Modify: `tests/test_rendering.py`
  Responsibility: exact rendering expectations in Russian.
- Modify: `tests/test_handlers.py`
  Responsibility: exact handler result text/button expectations in Russian.
- Modify: `tests/test_telegram_runtime.py`
  Responsibility: exact recovery/runtime message expectations in Russian.

### Task 1: Render Russian List Copy

**Files:**
- Modify: `src/grocery_bot/rendering.py`
- Test: `tests/test_rendering.py`

- [ ] **Step 1: Write the failing test**

Add/update a rendering test asserting exact Russian output:

```python
assert render_list_text(items) == "Список покупок\n\nНужно купить\n• молоко\n\nКуплено\n• хлеб"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_rendering.py -v`
Expected: FAIL because current text is English.

- [ ] **Step 3: Write minimal implementation**

Update rendering copy to:
- `Список покупок`
- `Нужно купить`
- `Куплено`
- `• Пока пусто.`
- `• Пока ничего не куплено.`

Update button labels to:
- `Куплено`
- `Удалить`
- `Вернуть`
- `Очистить купленное`

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_rendering.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/grocery_bot/rendering.py tests/test_rendering.py
git commit -m "feat: localize grocery list formatting to russian"
```

### Task 2: Align Handler And Runtime Copy

**Files:**
- Modify: `src/grocery_bot/handlers.py`
- Modify: `tests/test_handlers.py`
- Modify: `tests/test_telegram_runtime.py`

- [ ] **Step 1: Write the failing test**

Update exact-copy tests so handler/runtime messages are Russian:

```python
assert result.actions == [
    SendTextMessage(chat_id=10, text="Это действие больше не доступно.")
]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_handlers.py tests/test_telegram_runtime.py -v`
Expected: FAIL because current text is English.

- [ ] **Step 3: Write minimal implementation**

Update handler/runtime user-facing copy to Russian while preserving logic.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_handlers.py tests/test_telegram_runtime.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/grocery_bot/handlers.py tests/test_handlers.py tests/test_telegram_runtime.py
git commit -m "feat: localize handler messages to russian"
```

### Task 3: Full Verification

**Files:**
- Modify: any files required by verification fixes

- [ ] **Step 1: Run the full test suite**

Run: `.venv/bin/python -m pytest -v`
Expected: PASS

- [ ] **Step 2: Run compile check**

Run: `.venv/bin/python -m compileall src tests`
Expected: PASS

- [ ] **Step 3: Run validate-only startup**

Run: `BOT_TOKEN=test-token DATABASE_PATH=/tmp/grocery-bot-formatting.sqlite3 GROCERY_BOT_VALIDATE_ONLY=1 PYTHONPATH=src .venv/bin/python -m grocery_bot.main`
Expected: startup summary in Russian/working runtime, exit 0

- [ ] **Step 4: Fix any issues found and rerun checks**

Re-run failing commands first, then full verification.

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "test: verify russian grocery bot formatting"
```
