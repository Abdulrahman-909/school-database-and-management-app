"""
services/finance_service.py

All database operations for income and expenses (school-level finance,
not tied to any specific student). No UI code here - ui/finance.py
calls these functions instead of writing SQL directly.

IMPORTANT: totals here are calculated ONLY from the income/expenses
tables. Student fee payments (payments table) are handled separately
by payment_service.py and are NOT automatically folded into these
totals, to avoid double-counting tuition as generic "income".
"""


# ----------------------------------------------------------------------
# Income
# ----------------------------------------------------------------------

def get_all_income(db):
    return db.fetchall("SELECT * FROM income ORDER BY income_date DESC, id DESC;")


def get_income_by_id(db, income_id: int):
    return db.fetchone("SELECT * FROM income WHERE id = ?;", (income_id,))


def add_income(db, source, amount, income_date, note):
    amount_value = _validate_amount(amount)
    if not income_date or not str(income_date).strip():
        raise ValueError("Date is required.")

    return db.execute(
        "INSERT INTO income (source, amount, income_date, note) VALUES (?, ?, ?, ?);",
        (source, amount_value, str(income_date).strip(), note)
    )


def update_income(db, income_id, source, amount, income_date, note):
    amount_value = _validate_amount(amount)
    if not income_date or not str(income_date).strip():
        raise ValueError("Date is required.")

    db.execute(
        "UPDATE income SET source = ?, amount = ?, income_date = ?, note = ? WHERE id = ?;",
        (source, amount_value, str(income_date).strip(), note, income_id)
    )


def delete_income(db, income_id):
    db.execute("DELETE FROM income WHERE id = ?;", (income_id,))


def get_total_income(db) -> float:
    row = db.fetchone("SELECT COALESCE(SUM(amount), 0) AS total FROM income;")
    return row["total"]


# ----------------------------------------------------------------------
# Expenses
# ----------------------------------------------------------------------

def get_all_expenses(db):
    return db.fetchall("SELECT * FROM expenses ORDER BY expense_date DESC, id DESC;")


def get_expense_by_id(db, expense_id: int):
    return db.fetchone("SELECT * FROM expenses WHERE id = ?;", (expense_id,))


def add_expense(db, category, amount, expense_date, note):
    amount_value = _validate_amount(amount)
    if not expense_date or not str(expense_date).strip():
        raise ValueError("Date is required.")

    return db.execute(
        "INSERT INTO expenses (category, amount, expense_date, note) VALUES (?, ?, ?, ?);",
        (category, amount_value, str(expense_date).strip(), note)
    )


def update_expense(db, expense_id, category, amount, expense_date, note):
    amount_value = _validate_amount(amount)
    if not expense_date or not str(expense_date).strip():
        raise ValueError("Date is required.")

    db.execute(
        "UPDATE expenses SET category = ?, amount = ?, expense_date = ?, note = ? WHERE id = ?;",
        (category, amount_value, str(expense_date).strip(), note, expense_id)
    )


def delete_expense(db, expense_id):
    db.execute("DELETE FROM expenses WHERE id = ?;", (expense_id,))


def get_total_expenses(db) -> float:
    row = db.fetchone("SELECT COALESCE(SUM(amount), 0) AS total FROM expenses;")
    return row["total"]


# ----------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------

def get_finance_summary(db):
    """
    Returns income/expenses totals and the net balance BETWEEN THEM ONLY.
    Does not include student fee payments - see module docstring.
    """
    total_income = get_total_income(db)
    total_expenses = get_total_expenses(db)
    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_balance": total_income - total_expenses,
    }


def _validate_amount(amount):
    try:
        value = float(amount)
    except (TypeError, ValueError):
        raise ValueError("Amount must be a number.")
    if value <= 0:
        raise ValueError("Amount must be greater than zero.")
    return value