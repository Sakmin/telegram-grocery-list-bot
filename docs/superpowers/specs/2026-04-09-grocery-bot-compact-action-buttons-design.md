# Grocery Bot Compact Action Buttons Design

Date: 2026-04-09
Status: Approved by user in chat

## Goal

Make each grocery row use more horizontal space for the item name by shrinking the delete action and replacing action words with emoji labels.

## Scope

This change updates only the inline keyboard labels for list items.

It keeps the current button-first layout:
- the message body stays short
- item rows stay in the inline keyboard
- bought items remain visible
- `Очистить купленное` remains a separate bottom action

## Approved UX

### Item Row Labels

Each item row keeps two buttons:
- a wide primary action button with item text plus action emoji
- a compact delete button

The `<short item label>` part keeps the existing truncation behavior already used by the button-first list UI. This change only updates the action suffix and delete-button text.

For active items:
- `[<short item label> · ✅]`
- `[❌]`

For bought items:
- `[<short item label> · 🔙]`
- `[❌]`

### Width Behavior

The delete action should be as narrow as Telegram allows by using only the `❌` label.

Telegram controls actual button padding and layout, so there is no pixel-perfect width guarantee. The product intent is simply:
- maximize the width available to the primary item button
- minimize the width consumed by delete

### Bulk Action

The bottom bulk row stays textual:
- `Очистить купленное`

## Non-Goals

- No changes to callback payloads
- No changes to item ordering
- No changes to the message-body copy
- No changes to the truncation rule for item labels

## Testing Focus

- active item rows render `<item> · ✅` plus `❌`
- bought item rows render `<item> · 🔙` plus `❌`
- delete buttons are single-emoji labels
- `Очистить купленное` remains unchanged
