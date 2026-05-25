import sqlite3
from datetime import datetime
from database.db import get_db


def get_user_by_id(user_id):
    """Return user dict with name, email, member_since or None."""
    conn = get_db()
    row = conn.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    conn.close()

    if row is None:
        return None

    try:
        dt           = datetime.strptime(row["created_at"][:10], "%Y-%m-%d")
        member_since = dt.strftime("%B %Y")
    except (ValueError, TypeError):
        member_since = "Unknown"

    return {
        "name":         row["name"],
        "email":        row["email"],
        "member_since": member_since,
    }


def get_summary_stats(user_id, date_from=None, date_to=None):
    """Return total_spent, transaction_count, top_category."""
    conn   = get_db()
    params = [user_id]
    where  = "WHERE user_id = ?"

    if date_from and date_to:
        where  += " AND date BETWEEN ? AND ?"
        params += [date_from, date_to]

    row = conn.execute(
        f"SELECT SUM(amount), COUNT(*) FROM expenses {where}",
        params
    ).fetchone()

    total_spent       = row[0] or 0
    transaction_count = row[1] or 0

    top_row = conn.execute(
        f"""
        SELECT category
        FROM expenses {where}
        GROUP BY category
        ORDER BY SUM(amount) DESC
        LIMIT 1
        """,
        params
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


def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    """Return list of recent expenses newest-first."""
    conn   = get_db()
    params = [user_id]
    where  = "WHERE user_id = ?"

    if date_from and date_to:
        where  += " AND date BETWEEN ? AND ?"
        params += [date_from, date_to]

    params.append(limit)

    rows = conn.execute(
        f"""
        SELECT id, date, description, category, amount
        FROM expenses {where}
        ORDER BY date DESC, created_at DESC
        LIMIT ?
        """,
        params
    ).fetchall()
    conn.close()

    return [
        {
            "id":          row["id"],
            "date":        row["date"],
            "description": row["description"] or "—",
            "category":    row["category"],
            "amount":      f"₹{row['amount']:,.2f}",
        }
        for row in rows
    ]


def get_category_breakdown(user_id, date_from=None, date_to=None):
    """Return per-category totals with percentages summing to 100."""
    conn   = get_db()
    params = [user_id]
    where  = "WHERE user_id = ?"

    if date_from and date_to:
        where  += " AND date BETWEEN ? AND ?"
        params += [date_from, date_to]

    rows = conn.execute(
        f"""
        SELECT category, SUM(amount) AS total
        FROM expenses {where}
        GROUP BY category
        ORDER BY total DESC
        """,
        params
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

    pct_sum = sum(item["pct"] for item in result)
    if pct_sum != 100:
        result[0]["pct"] += (100 - pct_sum)

    return result

def insert_expense(user_id, amount, category, date, description):
    """Insert a new expense row. Expects pre-validated values."""
    conn = get_db()
    conn.execute(
        """
        INSERT INTO expenses (user_id, amount, category, date, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, amount, category, date, description),
    )
    conn.commit()
    conn.close()

def get_expense_by_id(expense_id, user_id):
    """Return expense row only if it belongs to user_id, else None."""
    conn = get_db()
    row  = conn.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id),
    ).fetchone()
    conn.close()
    return row


def update_expense(expense_id, user_id, amount, category, date, description):
    """Update an expense row. WHERE clause includes user_id for ownership safety."""
    conn = get_db()
    conn.execute(
        """
        UPDATE expenses
        SET amount = ?, category = ?, date = ?, description = ?
        WHERE id = ? AND user_id = ?
        """,
        (amount, category, date, description, expense_id, user_id),
    )
    conn.commit()
    conn.close()

def delete_expense(expense_id, user_id):
    """Delete an expense row. WHERE scoped to both id and user_id for ownership safety."""
    conn = get_db()
    conn.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id),
    )
    conn.commit()
    conn.close()