# Plan: Add Expense

## Overview
Upgrade the /expenses/add stub to a full GET+POST handler.
Add insert_expense() to queries.py. Create add_expense.html.
Add "Add Expense" button to profile.html and navbar.

---

## Step 1 — database/queries.py
Add insert_expense(user_id, amount, category, date, description):
- Accepts validated values only — no validation inside this helper
- Inserts into expenses table using parameterized query
- Calls get_db(), commits, closes connection
- Returns nothing

---

## Step 2 — app.py
Changes needed:
1. Import insert_expense from database.queries
2. Define VALID_CATEGORIES constant at top of file
3. Upgrade /expenses/add route:
   - methods=["GET", "POST"]
   - Both GET and POST: check session.get("user_id"), redirect to login if absent
   - GET: render add_expense.html with today's date pre-filled
   - POST validation sequence:
     a. Parse amount with float() — catch ValueError
     b. Check amount > 0
     c. Check category in VALID_CATEGORIES
     d. Parse date with datetime.strptime(value, "%Y-%m-%d") — catch ValueError
     e. Strip description, set to None if blank
     f. On any error: flash message, re-render form with submitted values
     g. On success: call insert_expense(), redirect to url_for("profile")

---

## Step 3 — templates/add_expense.html
Create new file extending base.html:
- Flash message block at top of form card
- amount: number input, step=0.01, min=0.01, required
- category: select with 7 fixed options
- date: date input, defaults to today, required
- description: text input, optional, maxlength=200
- Submit button: "Save Expense"
- Cancel link: url_for("profile")
- Pre-fill all fields with previously submitted values on error

---

## Step 4 — templates/profile.html
Add "Add Expense" button near the transaction table heading.

---

## Step 5 — templates/base.html
Add "Add Expense" link in navbar, visible only when
session.get("user_id") is set.

---

## Step 6 — static/css/style.css
Add styles for the add expense form page.

---

## Verify against Definition of Done
| Test | Expected |
|---|---|
| GET /expenses/add logged out | Redirect to /login |
| GET /expenses/add logged in | 200, form with all fields |
| POST valid data | Redirect to /profile, row in DB |
| POST missing amount | Re-render with error |
| POST amount = 0 | Re-render with error |
| POST invalid category | Re-render with error |
| POST invalid date | Re-render with error |
| POST no description | Redirect to /profile, NULL in DB |

## Files to change
| File | Changes |
|---|---|
| database/queries.py | Add insert_expense() |
| app.py | Import, constant, upgrade route |
| templates/profile.html | Add Expense button |
| templates/base.html | Add Expense navbar link |
| static/css/style.css | Add expense form styles |

## Files to create
| File | Purpose |
|---|---|
| templates/add_expense.html | Add expense form |
| tests/test_add_expense.py | Unit + route tests |