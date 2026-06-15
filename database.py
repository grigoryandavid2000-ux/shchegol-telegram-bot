from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "shchegol_bot.sqlite3"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS carts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                title TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price INTEGER,
                options_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                branch_id TEXT NOT NULL,
                pickup_time TEXT NOT NULL,
                total INTEGER,
                items_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'formed',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS loyalty (
                user_id INTEGER PRIMARY KEY,
                coffee_count INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            """
        )


def upsert_user(user_id: int, first_name: str | None = None, username: str | None = None) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO users (user_id, first_name, username)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                first_name = excluded.first_name,
                username = excluded.username,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, first_name, username),
        )
        conn.execute(
            "INSERT OR IGNORE INTO loyalty (user_id, coffee_count) VALUES (?, 0)",
            (user_id,),
        )


def ensure_user(user_id: int) -> None:
    with connect() as conn:
        conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.execute(
            "INSERT OR IGNORE INTO loyalty (user_id, coffee_count) VALUES (?, 0)",
            (user_id,),
        )


def get_cart(user_id: int) -> list[dict[str, Any]]:
    ensure_user(user_id)
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, item_id, title, quantity, unit_price, options_json
            FROM carts
            WHERE user_id = ?
            ORDER BY id
            """,
            (user_id,),
        ).fetchall()

    items: list[dict[str, Any]] = []
    for row in rows:
        options = json.loads(row["options_json"] or "{}")
        items.append(
            {
                "cart_id": row["id"],
                "item_id": row["item_id"],
                "title": row["title"],
                "quantity": row["quantity"],
                "unit_price": row["unit_price"],
                "options": options,
            }
        )
    return items


def add_cart_item(
    user_id: int,
    item_id: str,
    title: str,
    quantity: int,
    unit_price: int | None,
    options: dict[str, Any] | None = None,
) -> None:
    ensure_user(user_id)
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO carts (user_id, item_id, title, quantity, unit_price, options_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, item_id, title, quantity, unit_price, json.dumps(options or {}, ensure_ascii=False)),
        )


def upsert_cart_item(
    user_id: int,
    item_id: str,
    title: str,
    quantity: int,
    unit_price: int | None,
    options: dict[str, Any] | None = None,
) -> None:
    ensure_user(user_id)
    options_json = json.dumps(options or {}, ensure_ascii=False, sort_keys=True)
    with connect() as conn:
        existing = conn.execute(
            """
            SELECT id, quantity
            FROM carts
            WHERE user_id = ?
              AND item_id = ?
              AND IFNULL(unit_price, -1) = IFNULL(?, -1)
              AND options_json = ?
            ORDER BY id
            LIMIT 1
            """,
            (user_id, item_id, unit_price, options_json),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE carts SET quantity = quantity + ? WHERE id = ?",
                (quantity, existing["id"]),
            )
            return

        conn.execute(
            """
            INSERT INTO carts (user_id, item_id, title, quantity, unit_price, options_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, item_id, title, quantity, unit_price, options_json),
        )


def clear_cart(user_id: int) -> None:
    ensure_user(user_id)
    with connect() as conn:
        conn.execute("DELETE FROM carts WHERE user_id = ?", (user_id,))


def get_loyalty(user_id: int) -> int:
    ensure_user(user_id)
    with connect() as conn:
        row = conn.execute(
            "SELECT coffee_count FROM loyalty WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    return int(row["coffee_count"]) if row else 0


def increment_loyalty(user_id: int, amount: int) -> None:
    ensure_user(user_id)
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO loyalty (user_id, coffee_count)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                coffee_count = coffee_count + excluded.coffee_count,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, amount),
        )


def create_order(
    user_id: int,
    branch_id: str,
    pickup_time: str,
    total: int | None,
    items: list[dict[str, Any]],
) -> int:
    ensure_user(user_id)
    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO orders (user_id, branch_id, pickup_time, total, items_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, branch_id, pickup_time, total, json.dumps(items, ensure_ascii=False)),
        )
        return int(cursor.lastrowid)
