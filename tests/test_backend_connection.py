import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def get_seed_user_id():
    """Return the id of demo@spendly.com from the real DB."""
    from database.db import get_db
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
    ).fetchone()
    conn.close()
    return row["id"] if row else None


# ------------------------------------------------------------------ #
# get_user_by_id                                                      #
# ------------------------------------------------------------------ #

def test_get_user_by_id_valid():
    user_id = get_seed_user_id()
    result  = get_user_by_id(user_id)
    assert result is not None
    assert result["name"]  == "Demo User"
    assert result["email"] == "demo@spendly.com"
    assert "member_since" in result


def test_get_user_by_id_invalid():
    result = get_user_by_id(999999)
    assert result is None


# ------------------------------------------------------------------ #
# get_summary_stats                                                   #
# ------------------------------------------------------------------ #

def test_get_summary_stats_with_expenses():
    user_id = get_seed_user_id()
    result  = get_summary_stats(user_id)
    assert result["transaction_count"] == 8
    assert result["top_category"]      == "Bills"
    assert "₹" in result["total_spent"]


def test_get_summary_stats_no_expenses():
    result = get_summary_stats(999999)
    assert result["total_spent"]       == 0
    assert result["transaction_count"] == 0
    assert result["top_category"]      == "—"


# ------------------------------------------------------------------ #
# get_recent_transactions                                             #
# ------------------------------------------------------------------ #

def test_get_recent_transactions_with_expenses():
    user_id = get_seed_user_id()
    result  = get_recent_transactions(user_id)
    assert len(result) > 0
    for tx in result:
        assert "date"        in tx
        assert "description" in tx
        assert "category"    in tx
        assert "amount"      in tx
        assert "₹"           in tx["amount"]
    # Check newest-first ordering
    dates = [tx["date"] for tx in result]
    assert dates == sorted(dates, reverse=True)


def test_get_recent_transactions_no_expenses():
    result = get_recent_transactions(999999)
    assert result == []


# ------------------------------------------------------------------ #
# get_category_breakdown                                              #
# ------------------------------------------------------------------ #

def test_get_category_breakdown_with_expenses():
    user_id = get_seed_user_id()
    result  = get_category_breakdown(user_id)
    assert len(result) > 0
    # Percentages must sum to 100
    assert sum(item["pct"] for item in result) == 100
    # Must be ordered by amount descending
    for item in result:
        assert "name"   in item
        assert "amount" in item
        assert "pct"    in item
        assert isinstance(item["pct"], int)


def test_get_category_breakdown_no_expenses():
    result = get_category_breakdown(999999)
    assert result == []


# ------------------------------------------------------------------ #
# Route tests                                                         #
# ------------------------------------------------------------------ #

@pytest.fixture
def client():
    from app import app
    app.config["TESTING"]     = True
    app.config["SECRET_KEY"]  = "test-secret"
    with app.test_client() as client:
        yield client


def test_profile_unauthenticated_redirects(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_authenticated(client):
    user_id = get_seed_user_id()
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
    response = client.get("/profile")
    assert response.status_code == 200
    html = response.data.decode()
    assert "Demo User"        in html
    assert "demo@spendly.com" in html
    assert "₹"                in html
    assert "Bills"            in html