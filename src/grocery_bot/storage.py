from pathlib import Path
import sqlite3

from grocery_bot.models import GroceryItem, GroceryItemStatus, GroupList


class SQLiteStorage:
    def __init__(self, database_path: Path):
        self._database_path = Path(database_path)

    def initialize(self) -> None:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS groups (
                    group_id INTEGER PRIMARY KEY,
                    list_message_id INTEGER,
                    list_message_chat_id INTEGER,
                    is_pinned INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS items (
                    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    created_by_user_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    FOREIGN KEY(group_id) REFERENCES groups(group_id)
                );
                """
            )

    def ensure_group(self, group_id: int) -> GroupList:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO groups (group_id)
                VALUES (?)
                ON CONFLICT(group_id) DO NOTHING
                """,
                (group_id,),
            )
            row = connection.execute(
                """
                SELECT group_id, list_message_id, list_message_chat_id, is_pinned
                FROM groups
                WHERE group_id = ?
                """,
                (group_id,),
            ).fetchone()
        return self._group_from_row(row)

    def add_item(self, group_id: int, text: str, created_by_user_id: int) -> GroceryItem:
        self.ensure_group(group_id=group_id)
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO items (group_id, text, created_by_user_id)
                VALUES (?, ?, ?)
                """,
                (group_id, text, created_by_user_id),
            )
            row = connection.execute(
                """
                SELECT item_id, group_id, text, created_by_user_id, status
                FROM items
                WHERE item_id = ?
                """,
                (cursor.lastrowid,),
            ).fetchone()
        return self._item_from_row(row)

    def list_items(self, group_id: int) -> list[GroceryItem]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT item_id, group_id, text, created_by_user_id, status
                FROM items
                WHERE group_id = ?
                ORDER BY item_id ASC
                """,
                (group_id,),
            ).fetchall()
        return [self._item_from_row(row) for row in rows]

    def update_item_status(self, group_id: int, item_id: int, status: GroceryItemStatus) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE items
                SET status = ?
                WHERE group_id = ? AND item_id = ?
                """,
                (status.value, group_id, item_id),
            )

    def delete_item(self, group_id: int, item_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                DELETE FROM items
                WHERE group_id = ? AND item_id = ?
                """,
                (group_id, item_id),
            )

    def clear_done_items(self, group_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                DELETE FROM items
                WHERE group_id = ? AND status = ?
                """,
                (group_id, GroceryItemStatus.DONE.value),
            )

    def update_group_message(
        self,
        group_id: int,
        list_message_id: int | None,
        list_message_chat_id: int | None,
        is_pinned: bool,
    ) -> GroupList:
        self.ensure_group(group_id=group_id)
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE groups
                SET list_message_id = ?, list_message_chat_id = ?, is_pinned = ?
                WHERE group_id = ?
                """,
                (list_message_id, list_message_chat_id, int(is_pinned), group_id),
            )
            row = connection.execute(
                """
                SELECT group_id, list_message_id, list_message_chat_id, is_pinned
                FROM groups
                WHERE group_id = ?
                """,
                (group_id,),
            ).fetchone()
        return self._group_from_row(row)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _group_from_row(self, row: sqlite3.Row) -> GroupList:
        return GroupList(
            group_id=row["group_id"],
            list_message_id=row["list_message_id"],
            list_message_chat_id=row["list_message_chat_id"],
            is_pinned=bool(row["is_pinned"]),
        )

    def _item_from_row(self, row: sqlite3.Row) -> GroceryItem:
        return GroceryItem(
            item_id=row["item_id"],
            group_id=row["group_id"],
            text=row["text"],
            created_by_user_id=row["created_by_user_id"],
            status=GroceryItemStatus(row["status"]),
        )
