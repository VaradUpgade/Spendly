# Plan: Database Setup

## Files to change
1. `database/db.py` — implement get_db(), init_db(), seed_db()
2. `app.py` — import and call init_db() + seed_db() on startup

## Step-by-step
1. Implement get_db()
2. Implement init_db() with both table schemas
3. Implement seed_db() with duplicate guard
4. Update app.py imports and startup calls