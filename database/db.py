# Students will write this file in Step 1 — Database Setup
# This file should contain:
#   get_db()   — returns a SQLite connection with row_factory and foreign keys enabled
#   init_db()  — creates all tables using CREATE TABLE IF NOT EXISTS
#   seed_db()  — inserts sample data for development


import sqlite3
import os
from werkzeug.security import generate_password_hash

# Path to the database file — always in the project root
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spendly.db")


def get_db():
    """Open and return a database connection with row factory and FK enforcement."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables if they don't exist. Safe to call multiple times."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def seed_db():
    """Insert demo data only once. Returns early if data already exists."""
    conn = get_db()

    # Guard — don't seed if users already exist
    existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing > 0:
        conn.close()
        return

    # Insert demo user
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (
            "Demo User",
            "demo@spendly.com",
            generate_password_hash("demo123"),
        ),
    )

    # Get the demo user's id
    user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
    ).fetchone()[0]

    # Insert 8 sample expenses
    expenses = [
        (user_id, 1200.00, "Food",          "2026-05-01", "Grocery run"),
        (user_id,  450.00, "Transport",     "2026-05-02", "Monthly bus pass"),
        (user_id, 3500.00, "Bills",         "2026-05-03", "Electricity bill"),
        (user_id,  800.00, "Health",        "2026-05-05", "Pharmacy"),
        (user_id,  600.00, "Entertainment", "2026-05-08", "Movie night"),
        (user_id, 2200.00, "Shopping",      "2026-05-10", "New shoes"),
        (user_id,  350.00, "Food",          "2026-05-12", "Lunch with friend"),
        (user_id,  500.00, "Other",         "2026-05-14", "Miscellaneous"),
    ]

    conn.executemany(
        """
        INSERT INTO expenses (user_id, amount, category, date, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        expenses,
    )


    conn.commit()
    conn.close()

def create_user(name, email, password):
    """Insert a new user and return their id. Raises sqlite3.IntegrityError if email is taken."""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, generate_password_hash(password)),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def get_user_by_email(email):
    """Return the user row matching email, or None if not found."""
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    """Return the user row matching id, or None if not found."""
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return user