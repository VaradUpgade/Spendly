# Plan: Backend Connection for Profile Page

## Overview
Replace all hardcoded data in /profile with live SQLite queries.
Work is split across 3 parallel concerns, each handled independently,
then integrated into the single profile() route.

---

## Subagent 1 — Transaction History

### File: database/queries.py
Implement `get_recent_transactions(user_id, limit=10)`:
- Query expenses table WHERE user_id = ?
- ORDER BY date DESC, created_at DESC
- LIMIT by the limit parameter
- Return list of dicts: date, description, category, amount
- Amount formatted as ₹X,XXX.XX
- Return empty list if no expenses found

---

## Subagent 2 — Summary Stats

### File: database/queries.py
Implement `get_summary_stats(user_id)`:
- Query 1: SUM(amount), COUNT(*) FROM expenses WHERE user_id = ?
- Query 2: category with MAX total → GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1
- Return dict: total_spent (formatted ₹), transaction_count (int), top_category (string)
- If no expenses → return {"total_spent": 0, "transaction_count": 0, "top_category": "—"}

Also implement `get_user_by_id(user_id)` in queries.py:
- Query users table WHERE id = ?
- Format created_at as "Month YYYY" for member_since
- Return dict: name, email, member_since
- Return None if not found

---

## Subagent 3 — Category Breakdown

### File: database/queries.py
Implement `get_category_breakdown(user_id)`:
- Query: SELECT category, SUM(amount) FROM expenses WHERE user_id = ? GROUP BY category ORDER BY SUM(amount) DESC
- Calculate pct for each category: round(amount / total * 100)
- Adjust largest category to absorb rounding remainder so pcts sum to exactly 100
- Return list of dicts: name, amount (formatted ₹), pct (int)
- Return empty list if no expenses found

---

## Integration — app.py
After all 3 subagents complete:
1. Import all 4 helpers from database/queries.py
2. Remove get_user_by_id import from database.db (now lives in queries.py)
3. Replace hardcoded data in profile() with the 4 query calls
4. Keep auth guard: if not session.get("user_id") → redirect to login
5. Keep safety check: if db_user is None → clear session, redirect to login

---

## Step: Write Tests
File: tests/test_backend_connection.py
- Unit tests for all 4 query functions
- Route tests for GET /profile unauthenticated and authenticated

---

## Files to create
| File | Purpose |
|---|---|
| database/queries.py | All 4 query helper functions |
| tests/test_backend_connection.py | Unit + route tests |

## Files to change
| File | Changes |
|---|---|
| app.py | Import from queries.py, replace hardcoded data |