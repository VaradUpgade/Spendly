# Plan: Delete Expense

## Overview
Add delete_expense() to queries.py. Upgrade the
/expenses/<id>/delete stub to a POST-only handler.
Add Delete button to profile.html actions column.

---

## Step 1 — database/queries.py
Add delete_expense(expense_id, user_id):
- DELETE FROM expenses WHERE id = ? AND user_id = ?
- Both id AND user_id in WHERE — ownership guard
- Commits and closes connection
- Returns nothing, raises no errors

---

## Step 2 — app.py
1. Import delete_expense from database.queries
2. Replace the GET stub with POST-only handler:
   - methods=["POST"] only — GET returns 405 automatically
   - Check session.get("user_id") → redirect to login if absent
   - Call get_expense_by_id(id, session["user_id"])
   - If None → abort(404)
   - Call delete_expense(id, session["user_id"])
   - Redirect to url_for("profile")

---

## Step 3 — templates/profile.html
Inside the existing Actions <td>, add delete form
next to the existing Edit link:
- form method POST, action url_for with expense id
- style="display:inline" (only allowed exception)
- onsubmit confirm() dialog
- button class="btn-delete"

---

## Step 4 — static/css/style.css
Add .btn-delete style:
- Uses var(--danger) and var(--danger-light)
- Same shape as .tx-edit-link for visual consistency
- Hover inverts to solid danger background

---

## Verify against Definition of Done
| Test | Expected |
|---|---|
| POST logged out | Redirect to /login |
| POST own expense | Redirect to /profile, row gone |
| POST other user's expense | 404, row remains |
| POST non-existent id | 404 |
| GET /expenses/<id>/delete | 405 |

## Files to change
| File | Changes |
|---|---|
| database/queries.py | Add delete_expense() |
| app.py | Import, replace delete stub |
| templates/profile.html | Add Delete button in Actions td |
| static/css/style.css | Add .btn-delete styles |

## Files to create
| File | Purpose |
|---|---|
| tests/test_delete_expense.py | Unit + route tests |