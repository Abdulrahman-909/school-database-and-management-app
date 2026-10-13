"""
services/salary_service.py

All database operations for teacher salary payments. No UI code here -
ui/salaries.py calls these functions instead of writing SQL directly.
"""

from services import teacher_service


def get_all_salaries(db):
    """
    Returns all salary payments with the teacher's name joined in,
    newest first.
    """
    query = """
        SELECT sal.*, t.full_name AS teacher_name
        FROM salaries sal
        JOIN teachers t ON sal.teacher_id = t.id
        ORDER BY sal.payment_date DESC, sal.id DESC;
    """
    return db.fetchall(query)


def get_salary_by_id(db, salary_id: int):
    return db.fetchone("SELECT * FROM salaries WHERE id = ?;", (salary_id,))


def get_total_salaries_paid(db) -> float:
    row = db.fetchone("SELECT COALESCE(SUM(amount), 0) AS total FROM salaries;")
    return row["total"]


def get_teacher_base_salary(db, teacher_id: int):
    """
    Used by the UI to auto-fill the Amount field when a teacher is
    selected. Returns None if the teacher can't be found.
    """
    teacher = teacher_service.get_teacher_by_id(db, teacher_id)
    return teacher["salary_amount"] if teacher else None


def _validate_amount(amount):
    try:
        value = float(amount)
    except (TypeError, ValueError):
        raise ValueError("Amount must be a number.")
    if value <= 0:
        raise ValueError("Amount must be greater than zero.")
    return value


def add_salary(db, teacher_id, amount, payment_date, month, note):
    if teacher_id is None:
        raise ValueError("Please select a teacher.")
    if not payment_date or not str(payment_date).strip():
        raise ValueError("Payment date is required.")

    amount_value = _validate_amount(amount)

    return db.execute(
        """
        INSERT INTO salaries (teacher_id, amount, payment_date, month, note)
        VALUES (?, ?, ?, ?, ?);
        """,
        (teacher_id, amount_value, str(payment_date).strip(), month, note)
    )


def update_salary(db, salary_id, teacher_id, amount, payment_date, month, note):
    if teacher_id is None:
        raise ValueError("Please select a teacher.")
    if not payment_date or not str(payment_date).strip():
        raise ValueError("Payment date is required.")

    amount_value = _validate_amount(amount)

    db.execute(
        """
        UPDATE salaries
        SET teacher_id = ?, amount = ?, payment_date = ?, month = ?, note = ?
        WHERE id = ?;
        """,
        (teacher_id, amount_value, str(payment_date).strip(), month, note, salary_id)
    )


def delete_salary(db, salary_id):
    db.execute("DELETE FROM salaries WHERE id = ?;", (salary_id,))