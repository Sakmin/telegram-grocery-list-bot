# Grocery Bot Russian Formatting Design

Date: 2026-04-08
Status: Approved by user in chat

## Goal

Improve the grocery list message formatting so it feels native for a Russian-speaking user and reads more clearly in Telegram.

## Scope

This change updates only presentation and user-facing copy.

It does not change the core list model:
- bought items remain visible
- item-level buttons remain attached to each item row
- bulk cleanup remains available as a separate action

## Approved UX

### Message Text

The list message should be fully in Russian:
- title: `Список покупок`
- active section: `Нужно купить`
- bought section: `Куплено`

The current mixed English/Russian wording should be removed.

### Empty States

Empty-state text should also be in Russian:
- active empty state: `• Пока пусто.`
- bought empty state: `• Пока ничего не куплено.`

### Item Buttons

Buttons still appear in a separate inline keyboard area because of Telegram constraints, but they should conceptually stay tied to each item:
- active item actions: `Куплено`, `Удалить`
- bought item actions: `Вернуть`, `Удалить`

### Bulk Action

The bulk cleanup action should remain a single dedicated row at the bottom:
- `Очистить купленное`

It should only appear when there is at least one bought item.

## Non-Goals

- No categories
- No richer layout than Telegram supports
- No change to item ordering
- No change to duplicate handling logic
- No change to which actions are available

## Testing Focus

- Russian list text rendering
- Russian empty states
- Russian button labels
- `Очистить купленное` stays on the last row only when bought items exist
- Existing handler and runtime flows continue to work with the updated copy
