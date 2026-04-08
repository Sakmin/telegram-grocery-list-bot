from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest, TelegramError
from telegram.ext import (
    Application,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from grocery_bot.handlers import (
    EditListMessage,
    HandlerRequest,
    HandlerResult,
    PostListMessage,
    SendTextMessage,
    handle_callback,
    handle_list,
    handle_message,
    handle_start,
    refresh_list_message,
)
from grocery_bot.service import GroceryListService


TelegramHandlerCallback = Callable[[Update, CallbackContext], Awaitable[None]]


@dataclass(slots=True, frozen=True)
class TelegramHandlerRegistration:
    name: str
    handler: CommandHandler | MessageHandler | CallbackQueryHandler


def build_telegram_handlers(service: GroceryListService) -> tuple[TelegramHandlerRegistration, ...]:
    async def on_start(update: Update, context: CallbackContext) -> None:
        result = handle_start(service=service, request=_request_from_update(update))
        await execute_handler_result(
            bot=context.bot,
            service=service,
            group_id=update.effective_chat.id,
            result=result,
        )

    async def on_list(update: Update, context: CallbackContext) -> None:
        result = handle_list(service=service, request=_request_from_update(update))
        await execute_handler_result(
            bot=context.bot,
            service=service,
            group_id=update.effective_chat.id,
            result=result,
        )

    async def on_message(update: Update, context: CallbackContext) -> None:
        result = handle_message(service=service, request=_request_from_update(update))
        await execute_handler_result(
            bot=context.bot,
            service=service,
            group_id=update.effective_chat.id,
            result=result,
        )

    async def on_callback(update: Update, context: CallbackContext) -> None:
        callback_query = update.callback_query
        request = _request_from_update(update)
        try:
            result = handle_callback(service=service, request=request)
            await execute_handler_result(
                bot=context.bot,
                service=service,
                group_id=update.effective_chat.id,
                result=result,
            )
        finally:
            if callback_query is not None:
                await callback_query.answer()

    return (
        TelegramHandlerRegistration(
            name="start",
            handler=CommandHandler("start", on_start),
        ),
        TelegramHandlerRegistration(
            name="list",
            handler=CommandHandler("list", on_list),
        ),
        TelegramHandlerRegistration(
            name="message",
            handler=MessageHandler(filters.TEXT & ~filters.COMMAND, on_message),
        ),
        TelegramHandlerRegistration(
            name="callback",
            handler=CallbackQueryHandler(on_callback),
        ),
    )


def register_telegram_handlers(
    application: Application,
    registrations: tuple[TelegramHandlerRegistration, ...],
) -> None:
    for registration in registrations:
        application.add_handler(registration.handler)


async def execute_handler_result(
    bot,
    service: GroceryListService,
    group_id: int,
    result: HandlerResult,
) -> None:
    for action in result.actions:
        if isinstance(action, SendTextMessage):
            await bot.send_message(chat_id=action.chat_id, text=action.text)
        elif isinstance(action, PostListMessage):
            message = await bot.send_message(
                chat_id=action.chat_id,
                text=action.text,
                reply_markup=_build_reply_markup(action.reply_markup),
            )
            is_pinned = await _try_pin_message(
                bot=bot,
                chat_id=action.chat_id,
                message_id=message.message_id,
            )
            service.save_list_message(
                group_id=group_id,
                message_chat_id=action.chat_id,
                message_id=message.message_id,
                is_pinned=is_pinned,
            )
        elif isinstance(action, EditListMessage):
            try:
                await bot.edit_message_text(
                    chat_id=action.chat_id,
                    message_id=action.message_id,
                    text=action.text,
                    reply_markup=_build_reply_markup(action.reply_markup),
                )
            except BadRequest as error:
                if not _is_missing_message_error(error):
                    raise
                recovery_result = refresh_list_message(
                    service=service,
                    group_id=group_id,
                    missing_message_id=action.message_id,
                )
                await execute_handler_result(
                    bot=bot,
                    service=service,
                    group_id=group_id,
                    result=recovery_result,
                )


def _request_from_update(update: Update) -> HandlerRequest:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    callback_query = update.callback_query

    return HandlerRequest(
        chat_id=chat.id,
        user_id=user.id,
        chat_type=chat.type,
        text=message.text if message is not None else None,
        callback_data=callback_query.data if callback_query is not None else None,
    )


def _build_reply_markup(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup | None:
    if not rows:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=callback_data) for text, callback_data in row]
            for row in rows
        ]
    )


async def _try_pin_message(bot, chat_id: int, message_id: int) -> bool:
    try:
        await bot.pin_chat_message(
            chat_id=chat_id,
            message_id=message_id,
            disable_notification=True,
        )
    except TelegramError:
        return False
    return True


def _is_missing_message_error(error: BadRequest) -> bool:
    message = str(error).casefold()
    return "message to edit not found" in message or "message_id_invalid" in message

