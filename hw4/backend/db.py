"""SQLite access shared by the shop API, authentication, and agent tools."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data"
DB_PATH = Path(os.environ.get("CAMPUS_CUSTOMS_DB", str(DATA_ROOT / "campus_customs.db")))
PRODUCT_IMAGES = DATA_ROOT / "products"
SIZE_ORDER = {size: index for index, size in enumerate(("XS", "S", "M", "L", "XL", "XXL"))}


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    if not DB_PATH.is_file():
        raise FileNotFoundError(f"Missing catalogue database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database() -> None:
    with connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id_id ON chat_messages(user_id, id)")


def _to_product(row: sqlite3.Row, stock: list[dict]) -> dict:
    image_name = Path(row["image_file_path"]).name
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "search_tags": json.loads(row["search_tags"]),
        "image_url": f"/media/products/{image_name}",
        "price": row["price"],
        "inventory": stock,
        "total_stock": sum(item["quantity"] for item in stock),
    }


def read_products(product_id: str | None = None) -> list[dict]:
    with connection() as conn:
        if product_id is None:
            rows = conn.execute("SELECT * FROM catalogue ORDER BY name COLLATE NOCASE").fetchall()
        else:
            rows = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchall()
        if not rows:
            return []

        ids = [row["product_id"] for row in rows]
        placeholders = ",".join("?" for _ in ids)
        stock_rows = conn.execute(
            f"SELECT product_id, size, quantity FROM inventory WHERE product_id IN ({placeholders})",
            ids,
        ).fetchall()
        stock_by_product: dict[str, list[dict]] = {key: [] for key in ids}
        for row in stock_rows:
            stock_by_product[row["product_id"]].append(
                {"size": row["size"], "quantity": row["quantity"]}
            )
        for stock in stock_by_product.values():
            stock.sort(key=lambda item: (SIZE_ORDER.get(item["size"], 99), item["size"]))
        return [_to_product(row, stock_by_product[row["product_id"]]) for row in rows]


def read_product(product_id: str) -> dict | None:
    products = read_products(product_id)
    return products[0] if products else None


def read_chat_history(user_id: int, limit: int = 50) -> list[dict]:
    """Return recent persisted messages in display order for one signed-in user."""
    with connection() as conn:
        rows = conn.execute(
            """SELECT role, content, products_json, created_at FROM (
                   SELECT id, role, content, products_json, created_at
                   FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?
               ) ORDER BY id ASC""",
            (user_id, limit),
        ).fetchall()
        history = []
        for row in rows:
            try:
                products = json.loads(row["products_json"]) if row["products_json"] else []
            except json.JSONDecodeError:
                products = []
            history.append({
                "role": row["role"],
                "content": row["content"],
                "products": products,
                "created_at": row["created_at"],
            })
        return history


def save_chat_exchange(user_id: int, message: str, reply: str, products: list[dict]) -> None:
    """Commit the shopper message and the assistant reply together."""
    with connection() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)",
            (user_id, message),
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'assistant', ?, ?)",
            (user_id, reply, json.dumps(products, ensure_ascii=False)),
        )
