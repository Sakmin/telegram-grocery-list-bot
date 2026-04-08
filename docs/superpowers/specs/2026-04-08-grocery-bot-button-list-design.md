# Grocery Bot Button-First List Design

Date: 2026-04-08
Status: Approved by user in chat

## Goal

Replace the duplicated "text list + keyboard actions" layout with a button-first Telegram layout that feels cleaner and makes each grocery item actionable without reading the same list twice.

## Scope

This change updates only the pinned list presentation and its button labels.

It keeps the existing product behavior:
- one shared list per Telegram group
- active and bought items both remain visible
- item-level actions stay available for every item
- bulk cleanup for bought items stays available

## Approved UX

### Message Text

The message body becomes a short control panel instead of a full text rendering of the list.

Base header:
- `Список покупок`

When there are no active items:
- `Пока ничего не добавлено.`

When there are bought items:
- add a short text separator: `Куплено:`

The active list itself is no longer rendered as plain text lines in the message body.

### Item Buttons

The grocery list now lives in the inline keyboard.

For active items, each row contains:
- `[<short item name> · Куплено]`
- `[Удалить]`

For bought items, each row contains:
- `[<short item name> · Вернуть]`
- `[Удалить]`

This keeps the item name attached to the action so the keyboard remains understandable within Telegram's layout constraints.

### Label Shortening

The item name shown inside the action button should be compact:
- keep short names unchanged
- truncate long names to roughly 18-20 visible characters before the action suffix
- use ellipsis when truncation happens

Only the keyboard label is shortened. The stored item text in the database is not changed.

### Bulk Action

The bulk cleanup action remains a dedicated bottom row:
- `Очистить купленное`

It should only appear when there is at least one bought item.

## Non-Goals

- No changes to storage or item lifecycle
- No inline text rendering of the active list
- No categories, quantities parsing, or duplicate-merge redesign
- No changes to item ordering

## Testing Focus

- Message text for empty and non-empty states
- Keyboard rows include item names plus Russian action labels
- Long labels are truncated predictably
- Bought items stay visible and render after the `Куплено:` separator
- `Очистить купленное` remains the last row and only appears when needed
