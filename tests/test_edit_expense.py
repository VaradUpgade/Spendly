import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app as flask_app
from database.db import get_db


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


def get_first_expense(user_id):
    conn = get_db()
    row  = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? LIMIT 1",
        (user_id,)
    ).fetchone()
    conn.close()
    return row


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
# Unit tests — get_expense_by_id                                      #
# ------------------------------------------------------------------ #

def test_get_expense_by_id_valid():
    from database.queries import get_expense_by_id
    user_id = get_demo_user_id()
    expense = get_first_expense(user_id)
    result  = get_expense_by_id(expense["id"], user_id)
    assert result is not None
    assert result["id"] == expense["id"]


def test_get_expense_by_id_wrong_user():
    from database.queries import get_expense_by_id
    user_id = get_demo_user_id()
    expense = get_first_expense(user_id)
    result  = get_expense_by_id(expense["id"], 999999)
    assert result is None


def test_get_expense_by_id_nonexistent():
    from database.queries import get_expense_by_id
    result = get_expense_by_id(999999, 999999)
    assert result is None


# ------------------------------------------------------------------ #
# Unit tests — update_expense                                         #
# ------------------------------------------------------------------ #

def test_update_expense_correct_user():
    from database.queries import update_expense
    user_id = get_demo_user_id()
    expense = get_first_expense(user_id)
    update_expense(expense["id"], user_id, 99.0, "Food",
                   "2026-03-20", "Updated")
    conn = get_db()
    row  = conn.execute(
        "SELECT * FROM expenses WHERE id = ?", (expense["id"],)
    ).fetchone()
    conn.close()
    assert row["amount"] == 99.0
    assert row["description"] == "Updated"


def test_update_expense_wrong_user():
    from database.queries import update_expense, get_expense_by_id
    user_id = get_demo_user_id()
    expense = get_first_expense(user_id)
    original_amount = expense["amount"]
    update_expense(expense["id"], 999999, 1.0, "Food",
                   "2026-01-01", "Should not update")
    conn = get_db()
    row  = conn.execute(
        "SELECT * FROM expenses WHERE id = ?", (expense["id"],)
    ).fetchone()
    conn.close()
    assert row["amount"] == original_amount


# ------------------------------------------------------------------ #
# Route tests — GET /expenses/<id>/edit                               #
# ------------------------------------------------------------------ #

def test_get_edit_unauthenticated(client):
    user_id = get_demo_user_id()
    expense = get_first_expense(user_id)
    response = client.get(f"/expenses/{expense['id']}/edit")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_get_edit_authenticated_own(client):
    user_id = login(client)
    expense = get_first_expense(user_id)
    response = client.get(f"/expenses/{expense['id']}/edit")
    assert response.status_code == 200
    html = response.data.decode()
    assert "<form"    in html
    assert "POST"     in html
    assert "<select"  in html


def test_get_edit_other_user_expense(client):
    login(client)
    response = client.get("/expenses/999999/edit")
    assert response.status_code == 404


def test_get_edit_nonexistent(client):
    login(client)
    response = client.get("/expenses/999999/edit")
    assert response.status_code == 404


# ------------------------------------------------------------------ #
# Route tests — POST /expenses/<id>/edit                              #
# ------------------------------------------------------------------ #

def test_post_edit_unauthenticated(client):
    user_id = get_demo_user_id()
    expense = get_first_expense(user_id)
    response = client.post(f"/expenses/{expense['id']}/edit", data={
        "amount": "50", "category": "Food",
        "date": "2026-03-20", "description": "Test"
    })
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_post_edit_valid(client):
    user_id = login(client)
    expense = get_first_expense(user_id)
    response = client.post(f"/expenses/{expense['id']}/edit", data={
        "amount": "123.45", "category": "Shopping",
        "date": "2026-04-01", "description": "Updated desc"
    })
    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]
    conn = get_db()
    row  = conn.execute(
        "SELECT * FROM expenses WHERE id = ?", (expense["id"],)
    ).fetchone()
    conn.close()
    assert row["amount"]   == 123.45
    assert row["category"] == "Shopping"


def test_post_edit_other_user(client):
    login(client)
    response = client.post("/expenses/999999/edit", data={
        "amount": "50", "category": "Food",
        "date": "2026-03-20", "description": ""
    })
    assert response.status_code == 404


def test_post_edit_missing_amount(client):
    user_id = login(client)
    expense = get_first_expense(user_id)
    response = client.post(f"/expenses/{expense['id']}/edit", data={
        "amount": "", "category": "Food",
        "date": "2026-03-20", "description": ""
    })
    assert response.status_code == 200


def test_post_edit_zero_amount(client):
    user_id = login(client)
    expense = get_first_expense(user_id)
    response = client.post(f"/expenses/{expense['id']}/edit", data={
        "amount": "0", "category": "Food",
        "date": "2026-03-20", "description": ""
    })
    assert response.status_code == 200


def test_post_edit_non_numeric_amount(client):
    user_id = login(client)
    expense = get_first_expense(user_id)
    response = client.post(f"/expenses/{expense['id']}/edit", data={
        "amount": "abc", "category": "Food",
        "date": "2026-03-20", "description": ""
    })
    assert response.status_code == 200


def test_post_edit_invalid_category(client):
    user_id = login(client)
    expense = get_first_expense(user_id)
    response = client.post(f"/expenses/{expense['id']}/edit", data={
        "amount": "50", "category": "InvalidCat",
        "date": "2026-03-20", "description": ""
    })
    assert response.status_code == 200


def test_post_edit_invalid_date(client):
    user_id = login(client)
    expense = get_first_expense(user_id)
    response = client.post(f"/expenses/{expense['id']}/edit", data={
        "amount": "50", "category": "Food",
        "date": "not-a-date", "description": ""
    })
    assert response.status_code == 200


def test_post_edit_no_description(client):
    user_id = login(client)
    expense = get_first_expense(user_id)
    response = client.post(f"/expenses/{expense['id']}/edit", data={
        "amount": "50", "category": "Food",
        "date": "2026-03-20", "description": ""
    })
    assert response.status_code == 302
    conn = get_db()
    row  = conn.execute(
        "SELECT * FROM expenses WHERE id = ?", (expense["id"],)
    ).fetchone()
    conn.close()
    assert row["description"] is None