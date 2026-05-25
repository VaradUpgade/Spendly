import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app as flask_app
from database.db import get_db
from database.queries import insert_expense


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def get_demo_user_id():
    conn = get_db()
    row  = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
    ).fetchone()
    conn.close()
    return row["id"] if row else None


def create_test_expense(user_id):
    """Insert a fresh expense and return its id."""
    insert_expense(user_id, 99.0, "Other", "2026-04-01", "Test delete")
    conn = get_db()
    row  = conn.execute(
        """SELECT id FROM expenses
           WHERE user_id = ? AND description = ?
           ORDER BY id DESC LIMIT 1""",
        (user_id, "Test delete")
    ).fetchone()
    conn.close()
    return row["id"]


def expense_exists(expense_id):
    conn = get_db()
    row  = conn.execute(
        "SELECT id FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()
    conn.close()
    return row is not None


def login(client):
    user_id = get_demo_user_id()
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
    return user_id


# ------------------------------------------------------------------ #
# Fixtures                                                            #
# ------------------------------------------------------------------ #

@pytest.fixture
def client():
    flask_app.config["TESTING"]    = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    with flask_app.test_client() as client:
        yield client


# ------------------------------------------------------------------ #
# Unit tests — delete_expense                                         #
# ------------------------------------------------------------------ #

def test_delete_expense_correct_user():
    from database.queries import delete_expense
    user_id    = get_demo_user_id()
    expense_id = create_test_expense(user_id)
    assert expense_exists(expense_id)
    delete_expense(expense_id, user_id)
    assert not expense_exists(expense_id)


def test_delete_expense_wrong_user():
    from database.queries import delete_expense
    user_id    = get_demo_user_id()
    expense_id = create_test_expense(user_id)
    delete_expense(expense_id, 999999)   # wrong user — should do nothing
    assert expense_exists(expense_id)
    # cleanup
    from database.queries import delete_expense as de
    de(expense_id, user_id)


def test_delete_expense_nonexistent():
    from database.queries import delete_expense
    # Should not raise any error
    delete_expense(999999, 999999)


# ------------------------------------------------------------------ #
# Route tests                                                         #
# ------------------------------------------------------------------ #

def test_post_delete_unauthenticated(client):
    user_id    = get_demo_user_id()
    expense_id = create_test_expense(user_id)
    response   = client.post(f"/expenses/{expense_id}/delete")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    assert expense_exists(expense_id)
    # cleanup
    from database.queries import delete_expense
    delete_expense(expense_id, user_id)


def test_post_delete_own_expense(client):
    user_id    = login(client)
    expense_id = create_test_expense(user_id)
    assert expense_exists(expense_id)
    response   = client.post(f"/expenses/{expense_id}/delete")
    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]
    assert not expense_exists(expense_id)


def test_post_delete_other_user_expense(client):
    login(client)
    # Create expense under a different user id
    other_user_id = 999999
    conn = get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (get_demo_user_id(), 50.0, "Food", "2026-04-02", "Other user test")
    )
    conn.commit()
    row = conn.execute(
        "SELECT id FROM expenses WHERE description = ? ORDER BY id DESC LIMIT 1",
        ("Other user test",)
    ).fetchone()
    conn.close()
    expense_id = row["id"]

    # Try deleting as wrong user (999999 session)
    with client.session_transaction() as sess:
        sess["user_id"] = other_user_id
    response = client.post(f"/expenses/{expense_id}/delete")
    assert response.status_code == 404
    assert expense_exists(expense_id)
    # cleanup
    from database.queries import delete_expense
    delete_expense(expense_id, get_demo_user_id())


def test_post_delete_nonexistent(client):
    login(client)
    response = client.post("/expenses/999999/delete")
    assert response.status_code == 404


def test_get_delete_returns_405(client):
    login(client)
    user_id    = get_demo_user_id()
    expense_id = create_test_expense(user_id)
    response   = client.get(f"/expenses/{expense_id}/delete")
    assert response.status_code == 405
    # cleanup
    from database.queries import delete_expense
    delete_expense(expense_id, user_id)