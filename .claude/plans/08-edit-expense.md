# Plan: Edit Expense

## Overview
Upgrade the /expenses/<id>/edit stub to a full GET+POST handler.
Add get_expense_by_id() and update_expense() to queries.py.
Modify get_recent_transactions() to return expense id.
Create edit_expense.html. Add Edit link per row in profile.html.

---

## Step 1 — database/queries.py
Three changes:

1. Modify get_recent_transactions():
   - Add id to the SELECT column list

2. Add get_expense_by_id(expense_id, user_id):
   - SELECT * FROM expenses WHERE id = ? AND user_id = ?
   - Returns row or None
   - Ownership scoped at query level

3. Add update_expense(expense_id, user_id, amount, category, date, description):
   - UPDATE expenses SET ... WHERE id = ? AND user_id = ?
   - Both id AND user_id in WHERE clause — double ownership guard
   - Commits and closes connection

---

## Step 2 — app.py
1. Import get_expense_by_id and update_expense from database.queries
2. Replace /expenses/<int:id>/edit stub with GET+POST handler:
   - Both methods: check session.get("user_id") → redirect to login
   - GET:
     a. Call get_expense_by_id(id, session["user_id"])
     b. If None → abort(404)
     c. Render edit_expense.html with expense and categories
   - POST:
     a. Call get_expense_by_id(id, session["user_id"]) → abort(404) if None
     b. Validate amount, category, date (same rules as add expense)
     c. On error: flash, re-render form with submitted values
     d. On success: call update_expense(), redirect to url_for("profile")

---

## Step 3 — templates/edit_expense.html
Create new file extending base.html:
- Same structure as add_expense.html
- All fields pre-filled with expense values
- category select pre-selected to expense.category
- Submit button: "Save Changes"
- Cancel link: url_for("profile")
- Flash message block at top

---

## Step 4 — templates/profile.html
Two changes to the transaction table:
1. Add <th>Actions</th> to thead
2. Add Edit link cell per row using tx.id

---

## No new CSS needed
edit_expense.html reuses all classes from add_expense.html.

---

## Verify against Definition of Done
| Test | Expected |
|---|---|
| GET /expenses/<id>/edit logged out | Redirect to /login |
| GET own expense | 200, form pre-filled |
| GET other user's expense | 404 |
| GET non-existent id | 404 |
| POST logged out | Redirect to /login |
| POST valid data | Redirect to /profile, DB updated |
| POST other user's expense | 404 |
| POST missing/zero/non-numeric amount | 200, error shown |
| POST invalid category | 200, error shown |
| POST invalid date | 200, error shown |
| POST no description | Redirect to /profile, NULL in DB |

## Files to change
| File | Changes |
|---|---|
| database/queries.py | Add id to get_recent_transactions, add 2 new helpers |
| app.py | Import new helpers, upgrade edit route |
| templates/profile.html | Add Actions column + Edit links |

## Files to create
| File | Purpose |
|---|---|
| templates/edit_expense.html | Edit expense form |
| tests/test_edit_expense.py | Unit + route tests |