from dataclasses import dataclass

from grocery_bot.duplicate_detection import looks_like_duplicate
from grocery_bot.models import GroceryItem, GroceryItemStatus, GroupList
from grocery_bot.storage import SQLiteStorage


class ItemNotFoundError(LookupError):
    pass


class InvalidItemOperationError(ValueError):
    pass


@dataclass(slots=True, frozen=True)
class GroceryListSnapshot:
    group: GroupList
    items: list[GroceryItem]


class GroceryListService:
    def __init__(self, storage: SQLiteStorage):
        self._storage = storage

    def get_or_create_group(self, group_id: int) -> GroupList:
        return self._storage.ensure_group(group_id=group_id)

    def add_item(self, group_id: int, text: str, created_by_user_id: int) -> GroceryItem:
        self.get_or_create_group(group_id=group_id)
        return self._storage.add_item(
            group_id=group_id,
            text=text,
            created_by_user_id=created_by_user_id,
        )

    def find_duplicate_hints(self, group_id: int, text: str) -> list[GroceryItem]:
        return [
            item
            for item in self._storage.list_items(group_id=group_id)
            if item.status is GroceryItemStatus.ACTIVE and looks_like_duplicate(item.text, text)
        ]

    def mark_done(self, group_id: int, item_id: int, actor_user_id: int) -> GroceryItem:
        _ = actor_user_id
        item = self._get_item(group_id=group_id, item_id=item_id)
        if item.status is GroceryItemStatus.DONE:
            raise InvalidItemOperationError(f"item {item_id} is already done")
        self._storage.update_item_status(
            group_id=group_id,
            item_id=item_id,
            status=GroceryItemStatus.DONE,
        )
        return self._get_item(group_id=group_id, item_id=item_id)

    def return_item(self, group_id: int, item_id: int) -> GroceryItem:
        item = self._get_item(group_id=group_id, item_id=item_id)
        if item.status is GroceryItemStatus.ACTIVE:
            raise InvalidItemOperationError(f"item {item_id} is already active")
        self._storage.update_item_status(
            group_id=group_id,
            item_id=item_id,
            status=GroceryItemStatus.ACTIVE,
        )
        return self._get_item(group_id=group_id, item_id=item_id)

    def delete_item(self, group_id: int, item_id: int) -> GroceryItem:
        item = self._get_item(group_id=group_id, item_id=item_id)
        self._storage.delete_item(group_id=group_id, item_id=item_id)
        return item

    def clear_done_items(self, group_id: int) -> list[GroceryItem]:
        done_items = [
            item
            for item in self._storage.list_items(group_id=group_id)
            if item.status is GroceryItemStatus.DONE
        ]
        self._storage.clear_done_items(group_id=group_id)
        return done_items

    def get_snapshot(self, group_id: int) -> GroceryListSnapshot:
        group = self.get_or_create_group(group_id=group_id)
        items = self._storage.list_items(group_id=group_id)
        return GroceryListSnapshot(group=group, items=items)

    def save_list_message(
        self,
        group_id: int,
        message_chat_id: int,
        message_id: int,
        is_pinned: bool,
    ) -> GroupList:
        return self._storage.update_group_message(
            group_id=group_id,
            list_message_id=message_id,
            list_message_chat_id=message_chat_id,
            is_pinned=is_pinned,
        )

    def clear_list_message(
        self,
        group_id: int,
        expected_message_id: int | None = None,
    ) -> GroupList:
        group = self.get_or_create_group(group_id=group_id)
        if expected_message_id is not None and group.list_message_id != expected_message_id:
            return group
        return self._storage.update_group_message(
            group_id=group_id,
            list_message_id=None,
            list_message_chat_id=None,
            is_pinned=False,
        )

    def _get_item(self, group_id: int, item_id: int) -> GroceryItem:
        for item in self._storage.list_items(group_id=group_id):
            if item.item_id == item_id:
                return item
        raise ItemNotFoundError(f"item {item_id} does not exist in group {group_id}")
