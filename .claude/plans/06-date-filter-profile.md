# Plan: Date Filter for Profile Page

## Overview
Add date_from and date_to query params to GET /profile.
No new routes. Three files change: app.py, queries.py,
profile.html. One CSS file gets filter bar styles.

---

## Step 1 — database/queries.py
Add optional date_from and date_to params to all 3 helpers.

Pattern for each function:
- If both date_from and date_to are provided:
  append AND date BETWEEN ? AND ? to the WHERE clause
  add both values to the params tuple
- If either is None: query remains unchanged (no filter)

Functions to update:
1. get_summary_stats(user_id, date_from=None, date_to=None)
2. get_recent_transactions(user_id, limit=10, date_from=None, date_to=None)
3. get_category_breakdown(user_id, date_from=None, date_to=None)

---

## Step 2 — app.py
Changes to the profile() route:
1. Import datetime at the top
2. Read date_from and date_to from request.args
3. Validate each with datetime.strptime(value, "%Y-%m-%d")
   - On ValueError → treat as None (silent fallback)
4. If both valid but date_from > date_to:
   - flash("Start date must be before end date.")
   - set both to None (unfiltered)
5. Compute preset date ranges in Python:
   - This Month: first day of current month → today
   - Last 3 Months: today minus 90 days → today
   - Last 6 Months: today minus 180 days → today
   - All Time: no params
6. Pass date_from, date_to, and presets to template
7. Pass date_from and date_to to all 3 query helpers

---

## Step 3 — templates/profile.html
Add filter bar section above summary stats:
1. Four preset buttons as url_for links with date params
2. Custom range sub-form with two date inputs
3. Active state: compare current date_from/date_to
   against each preset range to highlight active button

---

## Step 4 — static/css/style.css
Add filter bar styles:
- .filter-bar, .filter-presets, .filter-btn
- .filter-btn.active (highlighted state)
- .filter-custom (date input row)
- All colors use CSS variables only

---

## Verify against Definition of Done
| Test | Expected |
|---|---|
| No params | Same as Step 5 unfiltered |
| This Month | Only current month expenses |
| Last 3 Months | 90-day window |
| Last 6 Months | 180-day window |
| All Time | All expenses, clean URL |
| Custom valid range | Only expenses in range |
| date_from > date_to | Flash error, unfiltered |
| Malformed date | Silent fallback, no crash |
| No expenses in range | ₹0.00, 0 transactions |