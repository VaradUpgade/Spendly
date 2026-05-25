import sqlite3
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
    insert_expense,
    get_expense_by_id,
    update_expense,
)
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "spendly-dev-secret-key"
VALID_CATEGORIES = [
    "Food", "Transport", "Bills",
    "Health", "Entertainment", "Shopping", "Other",
]
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
        return redirect(url_for("profile"))

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

@app.route("/analytics")
def analytics():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("analytics.html")


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = get_user_by_id(session["user_id"])
    if user is None:
        session.clear()
        return redirect(url_for("login"))

    # ── Date filter ────────────────────────────────────────────────
    def parse_date(value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except (ValueError, TypeError):
            return None

    date_from = parse_date(request.args.get("date_from", ""))
    date_to   = parse_date(request.args.get("date_to", ""))

    # If both present but range is inverted, flash and reset
    if date_from and date_to and date_from > date_to:
        flash("Start date must be before end date.")
        date_from = date_to = None

    # ── Preset ranges (computed in Python, not template) ───────────
    today      = date.today()
    first_of_month = today.replace(day=1)

    presets = {
        "this_month":   (first_of_month.strftime("%Y-%m-%d"),
                         today.strftime("%Y-%m-%d")),
        "last_3_months":(( today - timedelta(days=90)).strftime("%Y-%m-%d"),
                         today.strftime("%Y-%m-%d")),
        "last_6_months":(( today - timedelta(days=180)).strftime("%Y-%m-%d"),
                         today.strftime("%Y-%m-%d")),
        "all_time":     (None, None),
    }

    # ── Detect active preset ────────────────────────────────────────
    active_preset = "all_time"
    if date_from and date_to:
        active_preset = "custom"
        for key, (pf, pt) in presets.items():
            if key != "all_time" and date_from == pf and date_to == pt:
                active_preset = key
                break

    # ── Queries ─────────────────────────────────────────────────────
    uid          = session["user_id"]
    stats        = get_summary_stats(uid, date_from, date_to)
    transactions = get_recent_transactions(uid, limit=10,
                                           date_from=date_from,
                                           date_to=date_to)
    categories   = get_category_breakdown(uid, date_from, date_to)

    return render_template("profile.html",
        user          = user,
        stats         = stats,
        transactions  = transactions,
        categories    = categories,
        date_from     = date_from or "",
        date_to       = date_to   or "",
        presets       = presets,
        active_preset = active_preset,
    )


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    if request.method == "GET":
        today = date.today().strftime("%Y-%m-%d")
        return render_template("add_expense.html",
            categories=VALID_CATEGORIES,
            today=today,
            form={},
        )

    # POST — validate inputs
    form = {
        "amount":      request.form.get("amount", "").strip(),
        "category":    request.form.get("category", "").strip(),
        "date":        request.form.get("date", "").strip(),
        "description": request.form.get("description", "").strip(),
    }

    # 1. Amount — must be a positive number
    try:
        amount = float(form["amount"])
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash("Amount must be a number greater than 0.")
        return render_template("add_expense.html",
            categories=VALID_CATEGORIES,
            today=form["date"],
            form=form,
        )

    # 2. Category — must be from fixed list
    if form["category"] not in VALID_CATEGORIES:
        flash("Please select a valid category.")
        return render_template("add_expense.html",
            categories=VALID_CATEGORIES,
            today=form["date"],
            form=form,
        )

    # 3. Date — must be valid YYYY-MM-DD
    try:
        datetime.strptime(form["date"], "%Y-%m-%d")
    except ValueError:
        flash("Please enter a valid date.")
        return render_template("add_expense.html",
            categories=VALID_CATEGORIES,
            today=form["date"],
            form=form,
        )

    # 4. Description — optional
    description = form["description"] or None

    insert_expense(
        user_id=session["user_id"],
        amount=amount,
        category=form["category"],
        date=form["date"],
        description=description,
    )

    flash("Expense added successfully!")
    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    expense = get_expense_by_id(id, session["user_id"])
    if expense is None:
        abort(404)

    if request.method == "GET":
        return render_template("edit_expense.html",
            expense    = expense,
            expense_id = id,
            categories = VALID_CATEGORIES,
        )

    # POST — validate inputs
    form = {
        "amount":      request.form.get("amount", "").strip(),
        "category":    request.form.get("category", "").strip(),
        "date":        request.form.get("date", "").strip(),
        "description": request.form.get("description", "").strip(),
    }

    # 1. Amount
    try:
        amount = float(form["amount"])
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash("Amount must be a number greater than 0.")
        return render_template("edit_expense.html",
                expense    = form,
                expense_id = id,
                categories = VALID_CATEGORIES,
            )
    # 2. Category
    if form["category"] not in VALID_CATEGORIES:
        flash("Please select a valid category.")
        return render_template("edit_expense.html",
                expense    = form,
                expense_id = id,
                categories = VALID_CATEGORIES,
            )

    # 3. Date
    try:
        datetime.strptime(form["date"], "%Y-%m-%d")
    except ValueError:
        flash("Please enter a valid date.")
        return render_template("edit_expense.html",
                expense    = form,
                expense_id = id,
                categories = VALID_CATEGORIES,
            )

    # 4. Description — optional
    description = form["description"] or None

    update_expense(
        expense_id  = id,
        user_id     = session["user_id"],
        amount      = amount,
        category    = form["category"],
        date        = form["date"],
        description = description,
    )

    flash("Expense updated successfully!")
    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
