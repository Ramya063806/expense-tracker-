import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "expenses.db"


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                expense_date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "description": row["description"],
        "amount": row["amount"],
        "category": row["category"],
        "expense_date": row["expense_date"],
        "created_at": row["created_at"],
    }


def create_expense(
    description: str,
    amount: float,
    category: str,
    expense_date: date,
) -> dict:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO expenses (description, amount, category, expense_date)
            VALUES (?, ?, ?, ?)
            """,
            (description, amount, category, expense_date.isoformat()),
        )
        conn.commit()
        expense_id = cursor.lastrowid
        row = conn.execute(
            "SELECT * FROM expenses WHERE id = ?", (expense_id,)
        ).fetchone()
    return row_to_dict(row)


def list_expenses(
    category: Optional[str] = None,
    limit: int = 200,
) -> list[dict]:
    with get_connection() as conn:
        if category:
            rows = conn.execute(
                """
                SELECT * FROM expenses
                WHERE category = ?
                ORDER BY expense_date DESC, id DESC
                LIMIT ?
                """,
                (category, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM expenses
                ORDER BY expense_date DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    return [row_to_dict(r) for r in rows]


def get_expense(expense_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM expenses WHERE id = ?", (expense_id,)
        ).fetchone()
    return row_to_dict(row) if row else None


def get_expenses_by_ids(expense_ids: list[int]) -> list[dict]:
    if not expense_ids:
        return []
    placeholders = ",".join("?" * len(expense_ids))
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM expenses WHERE id IN ({placeholders})",
            expense_ids,
        ).fetchall()
    by_id = {row["id"]: row_to_dict(row) for row in rows}
    return [by_id[i] for i in expense_ids if i in by_id]


def delete_expense(expense_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM expenses WHERE id = ?", (expense_id,)
        )
        conn.commit()
    return cursor.rowcount > 0


def get_stats() -> dict:
    with get_connection() as conn:
        total_row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count FROM expenses"
        ).fetchone()
        category_rows = conn.execute(
            """
            SELECT category, SUM(amount) AS total
            FROM expenses
            GROUP BY category
            ORDER BY total DESC
            """
        ).fetchall()
    return {
        "total": float(total_row["total"]),
        "count": int(total_row["count"]),
        "by_category": {r["category"]: float(r["total"]) for r in category_rows},
    }
