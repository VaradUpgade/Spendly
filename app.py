import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "spendly-dev-secret-key"

# Initialise and seed the database on startup
with app.app_context():
    init_db()
    seed_db()

# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if session.get("user_id"):
            return redirect(url_for("landing"))
        return render_template("register.html")

    if request.method == "POST":
        name             = request.form.get("name", "").strip()
        email            = request.form.get("email", "").strip()
        password         = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # 1. Empty field check
        if not name or not email or not password or not confirm_password:
            flash("All fields are required.")
            return render_template("register.html")

        # 2. Password match check
        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("register.html")

        # 3. DB insert
        try:
            create_user(name, email, password)
            flash("Account created! Please sign in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered.")
            return render_template("register.html")

    abort(405)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("user_id"):
            return redirect(url_for("landing"))
        return render_template("login.html")

    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # 1. Empty field check
        if not email or not password:
            flash("Invalid email or password.")
            return render_template("login.html")

        # 2. User lookup
        user = get_user_by_email(email)
        if user is None:
            flash("Invalid email or password.")
            return render_template("login.html")

        # 3. Password verification
        if not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.")
            return render_template("login.html")

        # Success
        session["user_id"] = user["id"]
        return redirect(url_for("landing"))

    abort(405)


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = {
        "name":         "Demo User",
        "email":        "demo@spendly.com",
        "member_since": "January 2025",
    }

    stats = {
        "total_spent":       "₹18,240",
        "transaction_count": 34,
        "top_category":      "Food",
    }

    transactions = [
        {"date": "2026-05-14", "description": "Grocery run",        "category": "Food",          "amount": "₹1,200"},
        {"date": "2026-05-12", "description": "Electricity bill",   "category": "Bills",         "amount": "₹3,500"},
        {"date": "2026-05-10", "description": "New shoes",          "category": "Shopping",      "amount": "₹2,200"},
        {"date": "2026-05-08", "description": "Movie night",        "category": "Entertainment", "amount": "₹600"},
        {"date": "2026-05-05", "description": "Pharmacy",           "category": "Health",        "amount": "₹800"},
        {"date": "2026-05-02", "description": "Monthly bus pass",   "category": "Transport",     "amount": "₹450"},
    ]

    categories = [
        {"name": "Food",          "total": "₹4,800", "percentage": 65},
        {"name": "Bills",         "total": "₹3,500", "percentage": 48},
        {"name": "Shopping",      "total": "₹2,200", "percentage": 30},
        {"name": "Health",        "total": "₹1,800", "percentage": 25},
        {"name": "Entertainment", "total": "₹1,200", "percentage": 16},
        {"name": "Transport",     "total": "₹740",   "percentage": 10},
    ]

    return render_template("profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
