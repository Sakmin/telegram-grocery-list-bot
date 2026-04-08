# Grocery Telegram Bot MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an MVP Telegram bot for a shared grocery list in a group chat with one pinned list message, `+` and `/add` item creation, inline item actions, and per-group persistence.

**Architecture:** Use a small Python application with `python-telegram-bot`, a storage layer backed by SQLite, and a rendering layer that rebuilds the entire pinned list message after each change. Keep responsibilities split into focused modules: Telegram handlers, list service, persistence, and rendering/callback helpers.

**Tech Stack:** Python 3.12+, `python-telegram-bot`, SQLite, `pytest`

---

## Proposed File Structure

- Create: `pyproject.toml`
  Responsibility: project metadata and dependencies.
- Create: `.env.example`
  Responsibility: example runtime configuration.
- Create: `README.md`
  Responsibility: setup and local run instructions.
- Create: `src/grocery_bot/__init__.py`
  Responsibility: package marker.
- Create: `src/grocery_bot/config.py`
  Responsibility: environment variable loading and validation.
- Create: `src/grocery_bot/models.py`
  Responsibility: shared data models and enums.
- Create: `src/grocery_bot/storage.py`
  Responsibility: SQLite schema creation and CRUD operations.
- Create: `src/grocery_bot/duplicate_detection.py`
  Responsibility: simple duplicate hint logic for raw item text.
- Create: `src/grocery_bot/rendering.py`
  Responsibility: text rendering and inline keyboard construction.
- Create: `src/grocery_bot/service.py`
  Responsibility: core grocery list business logic.
- Create: `src/grocery_bot/handlers.py`
  Responsibility: Telegram message, command, and callback handlers.
- Create: `src/grocery_bot/main.py`
  Responsibility: application bootstrap and polling startup.
- Create: `tests/test_storage.py`
  Responsibility: persistence behavior.
- Create: `tests/test_duplicate_detection.py`
  Responsibility: duplicate hint rules.
- Create: `tests/test_rendering.py`
  Responsibility: list text and keyboard output.
- Create: `tests/test_service.py`
  Responsibility: business logic for item lifecycle and recovery behavior.
- Create: `tests/test_handlers.py`
  Responsibility: parsing and handler-level behaviors with light mocking.

## Assumptions To Validate During Execution

- Use one SQLite database file in the project directory, for example `data/grocery_bot.sqlite3`.
- Use polling for MVP instead of webhooks.
- Require bot admin rights only for pinning/editing the list message.
- Support one active grocery list per group chat.

### Task 1: Bootstrap The Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `README.md`
- Create: `src/grocery_bot/__init__.py`
- Create: `src/grocery_bot/main.py`

- [ ] **Step 1: Write the failing test**

Create a smoke test in `tests/test_handlers.py` that imports `grocery_bot.main` and asserts the application factory exists.

```python
from grocery_bot.main import build_application


def test_build_application_exists():
    assert callable(build_application)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_handlers.py::test_build_application_exists -v`
Expected: FAIL with `ModuleNotFoundError` or missing symbol.

- [ ] **Step 3: Write minimal implementation**

Create the package structure, dependency file, and a stub:

```python
def build_application():
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_handlers.py::test_build_application_exists -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .env.example README.md src/grocery_bot/__init__.py src/grocery_bot/main.py tests/test_handlers.py
git commit -m "chore: bootstrap grocery bot project"
```

### Task 2: Define Core Models And Configuration

**Files:**
- Create: `src/grocery_bot/config.py`
- Create: `src/grocery_bot/models.py`
- Modify: `src/grocery_bot/main.py`
- Test: `tests/test_service.py`

- [ ] **Step 1: Write the failing test**

Add a test for the item model and status enum:

```python
from grocery_bot.models import GroceryItemStatus, GroceryItem


def test_grocery_item_defaults_to_active():
    item = GroceryItem(item_id=1, group_id=10, text="Milk", created_by_user_id=20)
    assert item.status is GroceryItemStatus.ACTIVE
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_service.py::test_grocery_item_defaults_to_active -v`
Expected: FAIL because models do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add:
- `GroceryItemStatus` enum with `ACTIVE` and `DONE`
- `GroceryItem` dataclass
- `GroupList` dataclass
- config loader for `BOT_TOKEN` and `DATABASE_PATH`

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_service.py::test_grocery_item_defaults_to_active -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/grocery_bot/config.py src/grocery_bot/models.py src/grocery_bot/main.py tests/test_service.py
git commit -m "feat: add bot configuration and core models"
```

### Task 3: Implement SQLite Storage

**Files:**
- Create: `src/grocery_bot/storage.py`
- Test: `tests/test_storage.py`

- [ ] **Step 1: Write the failing test**

Add a test that creates a group list and stores one item:

```python
from grocery_bot.storage import SQLiteStorage


def test_storage_creates_group_and_item(tmp_path):
    storage = SQLiteStorage(tmp_path / "bot.sqlite3")
    storage.initialize()

    storage.ensure_group(group_id=123)
    item = storage.add_item(group_id=123, text="Milk", created_by_user_id=1)

    items = storage.list_items(group_id=123)
    assert [entry.text for entry in items] == ["Milk"]
    assert item.group_id == 123
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_storage.py::test_storage_creates_group_and_item -v`
Expected: FAIL because storage is not implemented.

- [ ] **Step 3: Write minimal implementation**

Implement:
- schema initialization
- group creation lookup
- item insertion
- item listing ordered by creation
- update item status
- delete item
- clear done items
- pinned/list message id persistence

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_storage.py -v`
Expected: PASS for the first storage scenario.

- [ ] **Step 5: Commit**

```bash
git add src/grocery_bot/storage.py tests/test_storage.py
git commit -m "feat: add sqlite storage for grocery lists"
```

### Task 4: Add Duplicate Hint Detection

**Files:**
- Create: `src/grocery_bot/duplicate_detection.py`
- Test: `tests/test_duplicate_detection.py`

- [ ] **Step 1: Write the failing test**

Add a normalization-based duplicate test:

```python
from grocery_bot.duplicate_detection import looks_like_duplicate


def test_duplicate_detection_ignores_case_and_spacing():
    assert looks_like_duplicate("Milk", " milk ")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_duplicate_detection.py::test_duplicate_detection_ignores_case_and_spacing -v`
Expected: FAIL because duplicate detection is missing.

- [ ] **Step 3: Write minimal implementation**

Implement a small helper that:
- trims whitespace
- collapses repeated spaces
- compares case-insensitively

Keep it intentionally simple for MVP.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_duplicate_detection.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/grocery_bot/duplicate_detection.py tests/test_duplicate_detection.py
git commit -m "feat: add duplicate hint detection"
```

### Task 5: Build The List Rendering Layer

**Files:**
- Create: `src/grocery_bot/rendering.py`
- Test: `tests/test_rendering.py`

- [ ] **Step 1: Write the failing test**

Add a rendering test:

```python
from grocery_bot.models import GroceryItem, GroceryItemStatus
from grocery_bot.rendering import render_list_text


def test_render_list_text_separates_active_and_done_items():
    items = [
        GroceryItem(item_id=1, group_id=1, text="Milk", created_by_user_id=1),
        GroceryItem(item_id=2, group_id=1, text="Bread", created_by_user_id=1, status=GroceryItemStatus.DONE),
    ]

    text = render_list_text(items)

    assert "Need to buy" in text
    assert "Bought" in text
    assert "Milk" in text
    assert "Bread" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_rendering.py::test_render_list_text_separates_active_and_done_items -v`
Expected: FAIL because rendering does not exist.

- [ ] **Step 3: Write minimal implementation**

Implement:
- list text rendering with `Need to buy` and `Bought` sections
- empty-state copy
- inline keyboard builder for item actions
- global `Clear bought` action

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_rendering.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/grocery_bot/rendering.py tests/test_rendering.py
git commit -m "feat: render grocery list messages and actions"
```

### Task 6: Implement Service-Layer Business Logic

**Files:**
- Create: `src/grocery_bot/service.py`
- Modify: `src/grocery_bot/storage.py`
- Modify: `src/grocery_bot/duplicate_detection.py`
- Test: `tests/test_service.py`

- [ ] **Step 1: Write the failing test**

Add a service-level lifecycle test:

```python
from grocery_bot.service import GroceryListService
from grocery_bot.storage import SQLiteStorage


def test_service_marks_item_done_and_returns_it(tmp_path):
    storage = SQLiteStorage(tmp_path / "bot.sqlite3")
    storage.initialize()
    service = GroceryListService(storage)

    item = service.add_item(group_id=1, text="Milk", created_by_user_id=10)
    service.mark_done(group_id=1, item_id=item.item_id, actor_user_id=10)
    updated = service.return_item(group_id=1, item_id=item.item_id)

    assert updated.status.value == "active"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_service.py::test_service_marks_item_done_and_returns_it -v`
Expected: FAIL because service methods are missing.

- [ ] **Step 3: Write minimal implementation**

Implement service methods for:
- create or load group state
- add item
- compute duplicate hints against active items
- mark done
- return item
- delete item
- clear done items
- fetch current list snapshot
- raise domain-specific errors for missing items or invalid operations

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/grocery_bot/service.py src/grocery_bot/storage.py src/grocery_bot/duplicate_detection.py tests/test_service.py
git commit -m "feat: add grocery list service layer"
```

### Task 7: Implement Telegram Handlers

**Files:**
- Create: `src/grocery_bot/handlers.py`
- Modify: `src/grocery_bot/main.py`
- Test: `tests/test_handlers.py`

- [ ] **Step 1: Write the failing test**

Add parsing tests for `+` and `/add`:

```python
from grocery_bot.handlers import extract_add_text


def test_extract_add_text_from_plus_prefix():
    assert extract_add_text("+ milk") == "milk"


def test_extract_add_text_from_add_command():
    assert extract_add_text("/add milk") == "milk"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_handlers.py::test_extract_add_text_from_plus_prefix tests/test_handlers.py::test_extract_add_text_from_add_command -v`
Expected: FAIL because handler helpers do not exist.

- [ ] **Step 3: Write minimal implementation**

Implement:
- add-item parsing
- group-only guard
- `/start` and `/list` behavior
- callback handlers for `Bought`, `Return`, `Delete`, and `Clear bought`
- helper that refreshes the list message after each state change
- recovery message when the pinned/list message is missing

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_handlers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/grocery_bot/handlers.py src/grocery_bot/main.py tests/test_handlers.py
git commit -m "feat: add telegram handlers for grocery list bot"
```

### Task 8: Wire Message Refresh And Pin Recovery

**Files:**
- Modify: `src/grocery_bot/handlers.py`
- Modify: `src/grocery_bot/service.py`
- Modify: `tests/test_handlers.py`
- Modify: `tests/test_service.py`

- [ ] **Step 1: Write the failing test**

Add a test that simulates a missing list message and expects a recovery notice path:

```python
def test_refresh_handles_missing_list_message(...):
    ...
```

Use mocks/stubs for Telegram API calls and assert the handler falls back to a recovery response instead of raising.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_handlers.py -k missing_list_message -v`
Expected: FAIL because recovery flow is incomplete.

- [ ] **Step 3: Write minimal implementation**

Implement:
- storage for `list_message_id`
- message edit-or-create flow
- explicit recovery messaging when edit/pin fails because the message no longer exists
- idempotent callback handling for repeated button presses

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_handlers.py tests/test_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/grocery_bot/handlers.py src/grocery_bot/service.py tests/test_handlers.py tests/test_service.py
git commit -m "feat: handle list message recovery and idempotent actions"
```

### Task 9: Finish End-To-End App Wiring And Docs

**Files:**
- Modify: `README.md`
- Modify: `src/grocery_bot/main.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write the failing test**

Add a smoke test:

```python
from grocery_bot.main import build_application


def test_build_application_returns_application_instance():
    app = build_application()
    assert app is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_handlers.py::test_build_application_returns_application_instance -v`
Expected: FAIL until the full application wiring is complete.

- [ ] **Step 3: Write minimal implementation**

Finalize:
- application builder
- handler registration
- startup initialization for the database
- README instructions for bot creation, env vars, install, and run

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_handlers.py::test_build_application_returns_application_instance -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md src/grocery_bot/main.py pyproject.toml tests/test_handlers.py
git commit -m "docs: finalize bot setup and application wiring"
```

### Task 10: Full Verification Before Completion

**Files:**
- Modify: any files required by bug fixes found during verification

- [ ] **Step 1: Run the full test suite**

Run: `pytest -v`
Expected: PASS

- [ ] **Step 2: Run a quick static sanity check**

Run: `python -m compileall src tests`
Expected: PASS with no syntax errors

- [ ] **Step 3: Start the bot locally with a test token placeholder**

Run: `python -m grocery_bot.main`
Expected: startup config validation or successful launch, depending on env vars

- [ ] **Step 4: Fix any issues found and rerun relevant checks**

Re-run only the failing commands first, then `pytest -v` again.

- [ ] **Step 5: Commit final verification fixes**

```bash
git add .
git commit -m "test: finish grocery bot MVP verification"
```

## Execution Notes

- Keep handlers thin; push business rules into `service.py`
- Keep storage operations small and explicit; avoid hidden side effects
- Use callback payloads that encode action and `item_id`
- Rebuild the full list message on every successful state change
- Do not add categories, natural language parsing, or merge automation in MVP
