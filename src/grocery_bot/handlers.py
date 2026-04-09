from dataclasses import dataclass, field
import re

from grocery_bot.rendering import build_list_keyboard, render_list_text
from grocery_bot.service import (
    GroceryListService,
    InvalidItemOperationError,
    ItemNotFoundError,
)

GROUP_ONLY_TEXT = "Этот бот работает только в группах."
RECOVERED_LIST_TEXT = "Сообщение со списком было удалено, поэтому я отправил новое."
STALE_ACTION_TEXT = "Это действие больше не доступно."
GROUP_CHAT_TYPES = {"group", "supergroup"}
ADD_COMMAND_PATTERN = re.compile(r"^/add(?:@\w+)?(?:\s+(.*))?$")


@dataclass(slots=True, frozen=True)
class HandlerRequest:
    chat_id: int
    user_id: int
    chat_type: str
    text: str | None = None
    callback_data: str | None = None
    missing_message_id: int | None = None


@dataclass(slots=True, frozen=True)
class CallbackAction:
    name: str
    item_id: int | None = None


@dataclass(slots=True, frozen=True)
class SendTextMessage:
    chat_id: int
    text: str


@dataclass(slots=True, frozen=True)
class AnswerCallback:
    text: str | None = None


@dataclass(slots=True, frozen=True)
class PostListMessage:
    chat_id: int
    text: str
    reply_markup: list[list[tuple[str, str]]]


@dataclass(slots=True, frozen=True)
class EditListMessage:
    chat_id: int
    message_id: int
    text: str
    reply_markup: list[list[tuple[str, str]]]


@dataclass(slots=True, frozen=True)
class HandlerResult:
    actions: list[SendTextMessage | AnswerCallback | PostListMessage | EditListMessage] = field(
        default_factory=list
    )


def extract_add_text(text: str | None) -> str | None:
    if text is None:
        return None

    stripped = text.strip()
    if stripped.startswith("+"):
        item_text = stripped[1:].strip()
        return item_text or None

    match = ADD_COMMAND_PATTERN.match(stripped)
    if match is None:
        return None

    item_text = (match.group(1) or "").strip()
    return item_text or None


def parse_callback_data(callback_data: str) -> CallbackAction:
    if callback_data == "clear_done":
        return CallbackAction(name="clear_done", item_id=None)

    action_name, separator, item_id_text = callback_data.partition(":")
    if separator != ":" or action_name not in {"done", "return", "delete"}:
        raise ValueError(f"unsupported callback data: {callback_data}")

    return CallbackAction(name=action_name, item_id=int(item_id_text))


def handle_start(service: GroceryListService, request: HandlerRequest) -> HandlerResult:
    return handle_list(service=service, request=request)


def handle_list(service: GroceryListService, request: HandlerRequest) -> HandlerResult:
    group_only_result = _group_only_result(request)
    if group_only_result is not None:
        return group_only_result

    return refresh_list_message(
        service=service,
        group_id=request.chat_id,
        missing_message_id=request.missing_message_id,
    )


def handle_message(service: GroceryListService, request: HandlerRequest) -> HandlerResult:
    group_only_result = _group_only_result(request)
    if group_only_result is not None:
        return group_only_result

    item_text = extract_add_text(request.text)
    if item_text is None:
        return HandlerResult()

    service.add_item(
        group_id=request.chat_id,
        text=item_text,
        created_by_user_id=request.user_id,
    )
    return refresh_list_message(
        service=service,
        group_id=request.chat_id,
        missing_message_id=request.missing_message_id,
    )


def handle_callback(service: GroceryListService, request: HandlerRequest) -> HandlerResult:
    group_only_result = _group_only_result(request)
    if group_only_result is not None:
        return group_only_result

    try:
        action = parse_callback_data(request.callback_data or "")
    except ValueError:
        return HandlerResult(actions=[AnswerCallback(text=STALE_ACTION_TEXT)])

    try:
        if action.name == "done":
            service.mark_done(
                group_id=request.chat_id,
                item_id=_require_item_id(action),
                actor_user_id=request.user_id,
            )
        elif action.name == "return":
            service.return_item(
                group_id=request.chat_id,
                item_id=_require_item_id(action),
            )
        elif action.name == "delete":
            service.delete_item(
                group_id=request.chat_id,
                item_id=_require_item_id(action),
            )
        elif action.name == "clear_done":
            service.clear_done_items(group_id=request.chat_id)
    except (InvalidItemOperationError, ItemNotFoundError):
        return HandlerResult(actions=[AnswerCallback(text=STALE_ACTION_TEXT)])

    return refresh_list_message(
        service=service,
        group_id=request.chat_id,
        missing_message_id=request.missing_message_id,
    )


def refresh_list_message(
    service: GroceryListService,
    group_id: int,
    missing_message_id: int | None = None,
) -> HandlerResult:
    recovery_actions: list[SendTextMessage] = []
    if missing_message_id is not None:
        snapshot = service.get_snapshot(group_id=group_id)
        if snapshot.group.list_message_id == missing_message_id:
            service.clear_list_message(
                group_id=group_id,
                expected_message_id=missing_message_id,
            )
            recovery_actions.append(
                SendTextMessage(chat_id=group_id, text=RECOVERED_LIST_TEXT)
            )

    snapshot = service.get_snapshot(group_id=group_id)
    if not _has_saved_list_message(
        snapshot.group.list_message_chat_id,
        snapshot.group.list_message_id,
    ):
        return HandlerResult(
            actions=[
                *recovery_actions,
                PostListMessage(
                    chat_id=group_id,
                    text=render_list_text(snapshot.items),
                    reply_markup=_render_reply_markup(snapshot.items),
                ),
            ]
        )

    return HandlerResult(
        actions=[
            *recovery_actions,
            EditListMessage(
                chat_id=snapshot.group.list_message_chat_id,
                message_id=snapshot.group.list_message_id,
                text=render_list_text(snapshot.items),
                reply_markup=_render_reply_markup(snapshot.items),
            )
        ]
    )


def _group_only_result(request: HandlerRequest) -> HandlerResult | None:
    if request.chat_type in GROUP_CHAT_TYPES:
        return None
    return HandlerResult(actions=[SendTextMessage(chat_id=request.chat_id, text=GROUP_ONLY_TEXT)])


def _has_saved_list_message(chat_id: int | None, message_id: int | None) -> bool:
    return chat_id is not None and message_id is not None


def _render_reply_markup(items) -> list[list[tuple[str, str]]]:
    keyboard = build_list_keyboard(items)
    return [
        [(button.text, button.callback_data) for button in row]
        for row in keyboard.inline_keyboard
    ]


def _require_item_id(action: CallbackAction) -> int:
    if action.item_id is None:
        raise ValueError(f"callback action {action.name} requires an item id")
    return action.item_id
