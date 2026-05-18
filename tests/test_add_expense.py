import pytest
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app as flask_app
from database.db import get_db, init_db


# ------------------------------------------------------------------ #
# Fixtures                                                            #
# ------------------------------------------------------------------ #

@pytest.fixture
def client():
    flask_app.config["TESTING"]   = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    with flask_app.test_client() as client:
        yield client


def get_demo_user_id():
    conn = get_db()
    row  = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
    ).fetchone()
    conn.close()
    return row["id"] if row else None


def login(client):
    user_id = get_demo_user_id()
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
    return user_id


# ------------------------------------------------------------------ #
# Unit tests — insert_expense                                         #
# ------------------------------------------------------------------ #

def test_insert_expense_with_description():
    from database.queries import insert_expense
    user_id = get_demo_user_id()
    insert_expense(user_id, 50.0, "Food", "2026-03-20", "Lunch")
    conn = get_db()
    row  = conn.execute(
        """SELECT * FROM expenses
           WHERE user_id=? AND amount=? AND category=? AND date=?
           ORDER BY id DESC LIMIT 1""",
        (user_id, 50.0, "Food", "2026-03-20")
    ).fetchone()
    conn.close()
    assert row is not None
    assert row["description"] == "Lunch"


def test_insert_expense_null_description():
    from database.queries import insert_expense
    user_id = get_demo_user_id()
    insert_expense(user_id, 100.0, "Transport", "2026-03-21", None)
    conn = get_db()
    row  = conn.execute(
        """SELECT * FROM expenses
           WHERE user_id=? AND amount=? AND category=? AND date=?
           ORDER BY id DESC LIMIT 1""",
        (user_id, 100.0, "Transport", "2026-03-21")
    ).fetchone()
    conn.close()
    assert row is not None
    assert row["description"] is None


# ------------------------------------------------------------------ #
# Route tests — GET /expenses/add                                     #
# ------------------------------------------------------------------ #

def test_get_add_expense_unauthenticated(client):
    response = client.get("/expenses/add")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_get_add_expense_authenticated(client):
    login(client)
    response = client.get("/expenses/add")
    assert response.status_code == 200
    html = response.data.decode()
    assert "<form"        in html
    assert "POST"         in html
    assert "Food"         in html
    assert "Transport"    in html
    assert "Bills"        in html
    assert "Health"       in html
    assert "Entertainment" in html
    assert "Shopping"     in html
    assert "Other"        in html


# ------------------------------------------------------------------ #
# Route tests — POST /expenses/add                                    #
# ------------------------------------------------------------------ #

def test_post_add_expense_unauthenticated(client):
    response = client.post("/expenses/add", data={
        "amount": "50", "category": "Food",
        "date": "2026-03-20", "description": "Lunch"
    })
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_post_add_expense_valid(client):
    user_id = login(client)
    response = client.post("/expenses/add", data={
        "amount": "50.0", "category": "Food",
        "date": "2026-03-20", "description": "Lunch"
    })
    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]
    conn = get_db()
    row  = conn.execute(
        "SELECT * FROM expenses WHERE user_id=? AND amount=? ORDER BY id DESC LIMIT 1",
        (user_id, 50.0)
    ).fetchone()
    conn.close()
    assert row is not None


def test_post_missing_amount(client):
    login(client)
    response = client.post("/expenses/add", data={
        "amount": "", "category": "Food",
        "date": "2026-03-20", "description": ""
    })
    assert response.status_code == 200
    assert b"Amount" in response.data or b"error" in response.data.lower()


def test_post_zero_amount(client):
    login(client)
    response = client.post("/expenses/add", data={
        "amount": "0", "category": "Food",
        "date": "2026-03-20", "description": ""
    })
    assert response.status_code == 200


def test_post_non_numeric_amount(client):
    login(client)
    response = client.post("/expenses/add", data={
        "amount": "abc", "category": "Food",
        "date": "2026-03-20", "description": ""
    })
    assert response.status_code == 200


def test_post_invalid_category(client):
    login(client)
    response = client.post("/expenses/add", data={
        "amount": "50", "category": "InvalidCat",
        "date": "2026-03-20", "description": ""
    })
    assert response.status_code == 200


def test_post_invalid_date(client):
    login(client)
    response = client.post("/expenses/add", data={
        "amount": "50", "category": "Food",
        "date": "not-a-date", "description": ""
    })
    assert response.status_code == 200


def test_post_no_description(client):
    user_id = login(client)
    today   = date.today().strftime("%Y-%m-%d")
    response = client.post("/expenses/add", data={
        "amount": "75.0", "category": "Other",
        "date": today, "description": ""
    })
    assert response.status_code == 302
    conn = get_db()
    row  = conn.execute(
        "SELECT * FROM expenses WHERE user_id=? AND amount=? ORDER BY id DESC LIMIT 1",
        (user_id, 75.0)
    ).fetchone()
    conn.close()
    assert row is not None
    assert row["description"] is None