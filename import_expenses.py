"""One-off script to import expenses from the provided Excel file into expenses.db."""
import sqlite3
import openpyxl
from pathlib import Path

XLSX = Path("/root/.claude/uploads/62eba256-7560-4bdd-b41c-0ea5566a2f0c/36eaf182-Expenses.xlsx")
DB = Path("expenses.db")

wb = openpyxl.load_workbook(XLSX, data_only=True)
ws = wb["Expenses"]

# Columns: Timestamp, Date, Amount, Merchant, Category, Business Purpose, Attendees, Receipt Photo
rows = []
for r in ws.iter_rows(min_row=2, values_only=True):
    date_val, amount, merchant, category, purpose, attendees, receipt_url = (
        r[1], r[2], r[3], r[4], r[5], r[6], r[7]
    )
    if not date_val or not merchant:
        continue

    expense_date = date_val.strftime("%Y-%m-%d") if hasattr(date_val, "strftime") else str(date_val)[:10]
    amount = float(amount) if amount else 0.0
    notes_parts = []
    if purpose and purpose != "NA":
        notes_parts.append(purpose)
    if attendees and attendees != "NA":
        notes_parts.append(f"Attendees: {attendees}")
    notes = " | ".join(notes_parts) or None
    clean_url = receipt_url if (receipt_url and str(receipt_url).startswith("http")) else None

    rows.append((merchant, amount, category or "Other", expense_date, notes, None, clean_url))

conn = sqlite3.connect(DB)
# Ensure receipt_url column exists
cols = [r[1] for r in conn.execute("PRAGMA table_info(expenses)").fetchall()]
if "receipt_url" not in cols:
    conn.execute("ALTER TABLE expenses ADD COLUMN receipt_url TEXT")

conn.executemany(
    "INSERT INTO expenses (title, amount, category, expense_date, notes, receipt, receipt_url) "
    "VALUES (?, ?, ?, ?, ?, ?, ?)",
    rows,
)
conn.commit()
conn.close()

print(f"Imported {len(rows)} expenses.")
