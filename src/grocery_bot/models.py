from dataclasses import dataclass, field
from enum import Enum


class GroceryItemStatus(str, Enum):
    ACTIVE = "active"
    DONE = "done"


@dataclass(slots=True)
class GroceryItem:
    item_id: int
    group_id: int
    text: str
    created_by_user_id: int
    status: GroceryItemStatus = field(default=GroceryItemStatus.ACTIVE)


@dataclass(slots=True)
class GroupList:
    group_id: int
    list_message_id: int | None = None
    list_message_chat_id: int | None = None
    is_pinned: bool = False
