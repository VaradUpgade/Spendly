import sqlite3
from datetime import datetime
from database.db import get_db


def get_user_by_id(user_id):
    """Return user dict with name, email, member_since or None if not found."""
    conn = get_db()
    row = conn.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    conn.close()

    if row is None:
        return None

    # Format "2026-01-15 10:30:00" → "January 2026"
    try:
        dt = datetime.strptime(row["created_at"][:10], "%Y-%m-%d")
        member_since = dt.strftime("%B %Y")
    except (ValueError, TypeError):
        member_since = "Unknown"

    return {
        "name":         row["name"],
        "email":        row["email"],
        "member_since": member_since,
    }


def get_summary_stats(user_id):
    """Return total_spent, transaction_count, top_category for a user."""
    conn = get_db()

    # Total spent and count
    row = conn.execute(
        "SELECT SUM(amount), COUNT(*) FROM expenses WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    total_spent       = row[0] or 0
    transaction_count = row[1] or 0

    # Top category
    top_row = conn.execute(
        """
        SELECT category
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY SUM(amount) DESC
        LIMIT 1
        """,
        (user_id,)
    ).fetchone()

    conn.close()

    if transaction_count == 0:
        return {
            "total_spent":       0,
            "transaction_count": 0,
            "top_category":      "—",
        }

    return {
        "total_spent":       f"₹{total_spent:,.2f}",
        "transaction_count": transaction_count,
        "top_category":      top_row["category"] if top_row else "—",
    }


def get_recent_transactions(user_id, limit=10):
    """Return list of recent expenses newest-first."""
    conn = get_db()
    rows = conn.execute(
        """
        SELECT date, description, category, amount
        FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC, created_at DESC
        LIMIT ?
        """,
        (user_id, limit)
    ).fetchall()
    conn.close()

    return [
        {
            "date":        row["date"],
            "description": row["description"] or "—",
            "category":    row["category"],
            "amount":      f"₹{row['amount']:,.2f}",
        }
        for row in rows
    ]


def get_category_breakdown(user_id):
    """Return per-category totals with percentages that sum to exactly 100."""
    conn = get_db()
    rows = conn.execute(
        """
        SELECT category, SUM(amount) AS total
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY total DESC
        """,
        (user_id,)
    ).fetchall()
    conn.close()

    if not rows:
        return []

    grand_total = sum(row["total"] for row in rows)

    result = [
        {
            "name":   row["category"],
            "amount": f"₹{row['total']:,.2f}",
            "pct":    round(row["total"] / grand_total * 100),
        }
        for row in rows
    ]

    # Adjust largest category so percentages sum to exactly 100
    pct_sum = sum(item["pct"] for item in result)
    if pct_sum != 100:
        result[0]["pct"] += (100 - pct_sum)

    return result