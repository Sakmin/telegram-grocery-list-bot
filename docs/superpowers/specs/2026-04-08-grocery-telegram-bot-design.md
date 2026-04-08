# Grocery Telegram Bot Design

Date: 2026-04-08
Status: Draft approved by user in chat

## Goal

Build a Telegram bot for a couple that manages one shared grocery list inside a group chat.

The MVP should feel fast and low-friction:
- users add items with `+ item text` or `/add item text`
- the bot maintains one pinned list message in the group
- users manage items with inline buttons
- the bot stays quiet in the chat and primarily updates the pinned message

## Users And Context

- Primary users: a couple
- Chat model: one shared Telegram group with the bot
- Collaboration model: any group participant can interact with the list in MVP

## Product Scope

### In Scope

- One persistent grocery list per Telegram group
- Add item via `+ ...`
- Add item via `/add ...`
- Render and update a pinned list message
- Mark item as bought
- Return bought item back to active
- Delete item
- Clear all bought items
- Soft duplicate hinting for likely duplicates
- Graceful handling when the pinned list message is missing

### Out Of Scope

- Personal lists in private chats
- Pair linking across separate chats
- Categories, stores, priorities, sorting rules
- Structured quantity parsing
- Full activity history
- Automatic duplicate merging
- Per-user permissions

## Recommended UX

### Main Interaction

Users talk to the bot in a group. To add an item they send:

- `+ milk`
- `+ bananas 1 kg`
- `/add coffee beans`

The bot stores the raw item text as entered and updates the shared pinned message.

### Pinned List Message

The list message is the primary interface and contains two sections:

1. `Need to buy`
2. `Bought`

Each active item shows buttons:

- `Bought`
- `Delete`

Each bought item shows buttons:

- `Return`
- `Delete`

The message also exposes a global action:

- `Clear bought`

### Chat Noise Policy

The bot should avoid sending separate event messages for routine changes. The main feedback loop is the updated pinned message.

### Duplicate Handling

If a newly added item looks very similar to an existing active item, the bot still adds it. The UI should show a gentle duplicate hint rather than blocking the action or auto-merging entries.

## Functional Requirements

### Group Setup

- The bot must support being added to a Telegram group
- The bot should be able to create and pin the grocery list message
- If the list message is unpinned or deleted, the bot should not silently recreate it
- Instead, the bot should notify the group that the list needs to be restored through an explicit recovery action

### Item Lifecycle

- New items are created in `active` status
- Pressing `Bought` changes status from `active` to `done`
- Pressing `Return` changes status from `done` to `active`
- Pressing `Delete` removes the item
- Pressing `Clear bought` removes all items in `done` status

### Input Rules

- Messages starting with `+` are treated as add-item input
- `/add` is an explicit add command
- Empty values like `+` or `/add` with no text should be rejected with a short helpful message
- Normal non-command chat messages should be ignored

## Data Model

### Group List

Each Telegram group should have one list record with:

- `group_id`
- `list_message_id`
- `list_message_chat_id` if needed by implementation
- `is_pinned` or recoverable pinned-state metadata if useful
- timestamps for creation and updates

### List Item

Each item should store:

- `item_id`
- `group_id`
- `text` as raw user-entered text
- `status` with values `active` or `done`
- `created_by_user_id`
- `created_at`
- `completed_by_user_id` nullable
- `completed_at` nullable
- duplicate hint metadata if the implementation needs it

## State And Rendering

- The bot should rebuild the full list view on every change
- It should then edit the single list message rather than patching partial fragments
- This keeps rendering simple and reduces edge-case complexity

Suggested rendering structure:

```text
Shopping List

Need to buy
- Milk
- Bananas 1 kg

Bought
- Bread
```

Inline buttons should map clearly to item actions and remain stable even when the rendered text changes.

## Error Handling

The bot must handle these cases gracefully:

- empty add request
- action on an already deleted item
- repeated button presses
- stale callbacks after the list changed
- missing or deleted pinned message
- insufficient bot permissions to edit or pin messages
- concurrent updates from multiple users

Expected behavior:

- do not crash
- return a short understandable response where needed
- keep stored data consistent

## MVP Success Criteria

After one week, the MVP is successful if:

- the couple finds it easy to quickly add and mark items
- the pinned message is enough to keep the shared list usable
- the bot is convenient enough to use regularly, even if smarter features are still missing

## Testing Focus

Priority scenarios for implementation and verification:

- add item through `+`
- add item through `/add`
- update the pinned list after each change
- mark bought
- return bought item to active
- delete item
- clear bought items
- isolate data between multiple groups
- recover gracefully when the pinned message is missing
- handle duplicate callbacks and concurrent interactions safely

## Notes For Implementation Planning

- Keep parsing intentionally simple in MVP
- Prefer predictable behavior over smart automation
- Build the bot around one clear source of truth per group
- Design callback payloads and storage so item actions remain robust as the list changes
