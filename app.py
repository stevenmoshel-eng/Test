import os
import sqlite3
from datetime import datetime, date
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for,
    send_from_directory, flash, abort,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

DB_PATH = Path("expenses.db")
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "pdf", "webp"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

CATEGORIES = [
    "Client Meals & Entertainment",
    "Travel",
    "Technology & Software",
    "Marketing & Prospecting",
    "Education & Training",
    "Mileage",
    "Other",
]


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                amount      REAL    NOT NULL,
                category    TEXT    NOT NULL,
                expense_date TEXT   NOT NULL,
                notes       TEXT,
                receipt     TEXT,
                receipt_url TEXT,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        # Migrate existing DB if receipt_url column is missing
        cols = [r[1] for r in conn.execute("PRAGMA table_info(expenses)").fetchall()]
        if "receipt_url" not in cols:
            conn.execute("ALTER TABLE expenses ADD COLUMN receipt_url TEXT")


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_receipt(file) -> str | None:
    if not file or file.filename == "":
        return None
    if not allowed_file(file.filename):
        flash("Receipt must be JPG, PNG, WEBP, or PDF.", "danger")
        return None
    filename = secure_filename(file.filename)
    # Prefix with timestamp to avoid collisions
    unique_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{filename}"
    file.save(UPLOAD_DIR / unique_name)
    return unique_name


def delete_receipt_file(filename: str):
    if filename:
        path = UPLOAD_DIR / filename
        if path.exists():
            path.unlink()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    category_filter = request.args.get("category", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")

    query = "SELECT * FROM expenses WHERE 1=1"
    params: list = []

    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)
    if date_from:
        query += " AND expense_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND expense_date <= ?"
        params.append(date_to)

    query += " ORDER BY expense_date DESC, id DESC"

    with get_db() as conn:
        expenses = conn.execute(query, params).fetchall()
        total = sum(e["amount"] for e in expenses)
        # Spending by category for the filtered set
        by_category = conn.execute(
            f"SELECT category, SUM(amount) as subtotal FROM expenses WHERE 1=1"
            + (" AND category = ?" if category_filter else "")
            + (" AND expense_date >= ?" if date_from else "")
            + (" AND expense_date <= ?" if date_to else "")
            + " GROUP BY category ORDER BY subtotal DESC",
            params,
        ).fetchall()

    return render_template(
        "index.html",
        expenses=expenses,
        total=total,
        by_category=by_category,
        categories=CATEGORIES,
        category_filter=category_filter,
        date_from=date_from,
        date_to=date_to,
    )


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        expense_date = request.form.get("expense_date", "").strip()
        notes = request.form.get("notes", "").strip()

        errors = []
        if not title:
            errors.append("Title is required.")
        try:
            amount = float(amount_raw)
            if amount < 0:
                errors.append("Amount must be non-negative.")
        except ValueError:
            amount = 0.0
            errors.append("Amount must be a number.")
        if not expense_date:
            errors.append("Date is required.")

        receipt_filename = None
        receipt_url = request.form.get("receipt_url", "").strip() or None
        if "receipt" in request.files:
            f = request.files["receipt"]
            if f and f.filename:
                if f.content_length and f.content_length > MAX_UPLOAD_BYTES:
                    errors.append("Receipt file must be under 10 MB.")
                else:
                    receipt_filename = save_receipt(f)

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("form.html", action="Add", categories=CATEGORIES,
                                   form=request.form)

        with get_db() as conn:
            conn.execute(
                "INSERT INTO expenses (title, amount, category, expense_date, notes, receipt, receipt_url) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (title, amount, category, expense_date, notes, receipt_filename, receipt_url),
            )
        flash("Expense added.", "success")
        return redirect(url_for("index"))

    today = date.today().isoformat()
    return render_template("form.html", action="Add", categories=CATEGORIES,
                           form={"expense_date": today})


@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit(expense_id: int):
    with get_db() as conn:
        expense = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    if not expense:
        abort(404)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        expense_date = request.form.get("expense_date", "").strip()
        notes = request.form.get("notes", "").strip()
        remove_receipt = request.form.get("remove_receipt") == "1"

        errors = []
        if not title:
            errors.append("Title is required.")
        try:
            amount = float(amount_raw)
            if amount < 0:
                errors.append("Amount must be non-negative.")
        except ValueError:
            amount = 0.0
            errors.append("Amount must be a number.")
        if not expense_date:
            errors.append("Date is required.")

        new_receipt = expense["receipt"]
        new_receipt_url = request.form.get("receipt_url", "").strip() or expense["receipt_url"]

        if remove_receipt:
            delete_receipt_file(expense["receipt"])
            new_receipt = None
            new_receipt_url = None

        if "receipt" in request.files:
            f = request.files["receipt"]
            if f and f.filename:
                saved = save_receipt(f)
                if saved:
                    delete_receipt_file(new_receipt)
                    new_receipt = saved

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("form.html", action="Edit", categories=CATEGORIES,
                                   form=request.form, expense=expense)

        with get_db() as conn:
            conn.execute(
                "UPDATE expenses SET title=?, amount=?, category=?, expense_date=?, "
                "notes=?, receipt=?, receipt_url=? WHERE id=?",
                (title, amount, category, expense_date, notes, new_receipt, new_receipt_url, expense_id),
            )
        flash("Expense updated.", "success")
        return redirect(url_for("index"))

    return render_template("form.html", action="Edit", categories=CATEGORIES,
                           form=expense, expense=expense)


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete(expense_id: int):
    with get_db() as conn:
        expense = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
        if not expense:
            abort(404)
        delete_receipt_file(expense["receipt"])
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    flash("Expense deleted.", "success")
    return redirect(url_for("index"))


@app.route("/receipt/<path:filename>")
def receipt(filename: str):
    safe = secure_filename(filename)
    if safe != filename:
        abort(404)
    return send_from_directory(UPLOAD_DIR, safe)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
