# Plan: Profile Page

## Overview
Replace the /profile stub with a fully designed profile page
showing hardcoded data. No DB queries in this step — UI only.

---

## Step 1 — `app.py`
Changes needed:
1. Replace the profile stub with a real view function
2. Add authentication guard at the top:
   - if not session.get("user_id") → redirect to url_for("login")
3. Pass hardcoded context to profile.html:
   - user: dict with name, email, member_since
   - stats: dict with total_spent, transaction_count, top_category
   - transactions: list of dicts with date, description, category, amount
   - categories: list of dicts with name, total, percentage

---

## Step 2 — `templates/profile.html`
Create a new file extending base.html with four sections:

Section 1 — User Info Card:
- Avatar circle showing initials (from name)
- Name, email, member since date
- Use .profile-avatar, .profile-card classes

Section 2 — Summary Stats Row:
- Three stat cards: Total Spent, Transactions, Top Category
- Use .stats-row, .stat-card classes

Section 3 — Transaction History Table:
- Columns: Date, Description, Category, Amount
- Category shown as a colored badge using CSS class not inline style
- At least 5 hardcoded rows
- Use .tx-table class

Section 4 — Category Breakdown:
- Per-category row with name, progress bar, total amount
- Use .category-breakdown, .breakdown-row classes

---

## Step 3 — `static/css/style.css`
Add new CSS sections for:
- .profile-card, .profile-avatar, .profile-info
- .stats-row, .stat-card, .stat-value, .stat-label
- .tx-table and all child elements
- .category-badge and per-category color variants
- .breakdown-row, .breakdown-bar, .breakdown-fill

All colors must use CSS variables only — no hardcoded hex.

---

## Step 4 — Verify against Definition of Done

| Test | Expected |
|---|---|
| GET /profile logged out | Redirect to /login |
| GET /profile logged in | HTTP 200, page renders |
| User info card | Name and email visible |
| Stats row | 3 stat values visible |
| Transaction table | At least 3 rows |
| Category breakdown | At least 3 categories |
| No hex values in profile.html | Only CSS variables used |

---

## Files to change
| File | Changes |
|---|---|
| `app.py` | Replace /profile stub with real view + hardcoded data |
| `static/css/style.css` | Add profile page styles |

## Files to create
| File | Purpose |
|---|---|
| `templates/profile.html` | Full profile page template |