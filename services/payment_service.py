"""
services/payment_service.py

All database operations for student payments, and the ONE authoritative
calculation of monthly and annual Total Fee / Paid / Remaining for a
student. Every other screen (Dashboard, Reports, Excel export, Receipt)
should call get_fee_summary() from here rather than recalculating this
logic separately.

IMPORTANT (fee model): the amount in fee_structures is now interpreted
as a MONTHLY fee, not an annual one. The annual total is always
monthly_fee x 12, calculated here - never typed in or stored directly.
Every payment is tagged with one of the 12 Afghan solar months so that
each month can be tracked/paid independently (a student can be fully
paid for Hamal while still owing for Sawr, etc.).
"""

from services import student_service
from services import fee_structure_service


# School year runs Hamal through Qaws (9 months) - Jadi, Dalw, and Hoot
# are winter break and are not part of the regular school fee calendar.
MONTH_NAMES = [
    "حمل", "ثور", "جوزا", "سرطان", "اسد", "سنبله",
    "میزان", "عقرب", "قوس",
]

MONTHS_PER_YEAR = len(MONTH_NAMES)  # 9


def _get_monthly_fee_for_student(db, student, academic_year):
    """
    A student's monthly fee, in this priority order:
    1. Their own custom_monthly_fee, if one is set (e.g. poverty or
       sibling discount) - this OVERRIDES the class fee entirely.
    2. Otherwise, the normal fee for their class + year.
    Every calculation in this file (annual summary, monthly breakdown,
    overpayment checks) goes through this one function, so a custom
    fee is automatically respected everywhere without any other
    changes needed.
    """
    if "custom_monthly_fee" in student.keys() and student["custom_monthly_fee"] is not None:
        return student["custom_monthly_fee"]

    if student["class_id"] is None:
        return None
    return fee_structure_service.get_fee_amount(db, student["class_id"], academic_year)


def get_fee_summary(db, student_id: int, academic_year: str):
    """
    Annual summary for a student:
        {
            "student": <row>,
            "fee_defined": bool,
            "monthly_fee": float,   # per-month amount from Fee Structure
            "total_fee": float,     # monthly_fee x 12
            "total_paid": float,    # sum of ALL payments this year, any month
            "remaining": float,
        }
    """
    student = student_service.get_student_by_id(db, student_id)
    if student is None:
        raise ValueError("Student not found.")

    monthly_fee = _get_monthly_fee_for_student(db, student, academic_year)
    fee_defined = monthly_fee is not None
    annual_fee = (monthly_fee * MONTHS_PER_YEAR) if fee_defined else 0.0

    total_paid = get_total_paid(db, student_id, academic_year)
    remaining = annual_fee - total_paid

    return {
        "student": student,
        "fee_defined": fee_defined,
        "monthly_fee": monthly_fee if fee_defined else 0.0,
        "total_fee": annual_fee,
        "total_paid": total_paid,
        "remaining": remaining,
    }


def get_month_summary(db, student_id: int, academic_year: str, month: str):
    """
    Summary for ONE month: {month, fee_defined, due, paid, remaining}.
    """
    student = student_service.get_student_by_id(db, student_id)
    if student is None:
        raise ValueError("Student not found.")

    monthly_fee = _get_monthly_fee_for_student(db, student, academic_year)
    fee_defined = monthly_fee is not None

    row = db.fetchone(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM payments "
        "WHERE student_id = ? AND academic_year = ? AND month = ?;",
        (student_id, academic_year, month)
    )
    paid = row["total"]
    due = monthly_fee if fee_defined else 0.0
    remaining = due - paid

    return {
        "month": month,
        "fee_defined": fee_defined,
        "due": due,
        "paid": paid,
        "remaining": remaining,
    }


def get_month_breakdown(db, student_id: int, academic_year: str):
    """Returns a list of get_month_summary() results, one per month, in order."""
    return [get_month_summary(db, student_id, academic_year, m) for m in MONTH_NAMES]


def get_total_paid(db, student_id: int, academic_year: str) -> float:
    row = db.fetchone(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM payments WHERE student_id = ? AND academic_year = ?;",
        (student_id, academic_year)
    )
    return row["total"]


def get_total_paid_all_students(db) -> float:
    row = db.fetchone("SELECT COALESCE(SUM(amount), 0) AS total FROM payments;")
    return row["total"]


def get_payments_for_student(db, student_id: int, academic_year: str = None):
    if academic_year:
        return db.fetchall(
            "SELECT * FROM payments WHERE student_id = ? AND academic_year = ? ORDER BY payment_date DESC, id DESC;",
            (student_id, academic_year)
        )
    return db.fetchall(
        "SELECT * FROM payments WHERE student_id = ? ORDER BY payment_date DESC, id DESC;",
        (student_id,)
    )


def get_payment_by_id(db, payment_id: int):
    return db.fetchone("SELECT * FROM payments WHERE id = ?;", (payment_id,))


def get_students_with_remaining_fees(db, academic_year: str):
    """
    Active students who owe money for this year (annual remaining > 0
    and a fee is actually defined). Uses get_fee_summary(), so this
    automatically reflects the monthly x 12 model with no extra logic.
    """
    students = db.fetchall("SELECT id FROM students WHERE status = 'active';")

    results = []
    for row in students:
        summary = get_fee_summary(db, row["id"], academic_year)
        if summary["fee_defined"] and summary["remaining"] > 0:
            results.append(summary)

    results.sort(key=lambda s: s["remaining"], reverse=True)
    return results


def _validate_amount(amount):
    try:
        value = float(amount)
    except (TypeError, ValueError):
        raise ValueError("Payment amount must be a number.")
    if value <= 0:
        raise ValueError("Payment amount must be greater than zero.")
    return value


def add_payment(db, student_id, amount, payment_date, academic_year, month,
                 note, received_by, allow_overpayment=False):
    if student_id is None:
        raise ValueError("Please select a student.")
    if not academic_year or not str(academic_year).strip():
        raise ValueError("Academic year is required.")
    if not month or month not in MONTH_NAMES:
        raise ValueError("Please select a valid month.")
    if not payment_date or not str(payment_date).strip():
        raise ValueError("Payment date is required.")

    academic_year = str(academic_year).strip()
    amount_value = _validate_amount(amount)

    # Overpayment protection is now PER MONTH: paying off Hamal in full
    # does not block payments for Sawr, Jawza, etc.
    month_summary = get_month_summary(db, student_id, academic_year, month)
    if month_summary["fee_defined"] and not allow_overpayment:
        new_total = month_summary["paid"] + amount_value
        if new_total > month_summary["due"]:
            over_by = new_total - month_summary["due"]
            raise ValueError(
                f"This payment would exceed {month}'s fee by {over_by:,.0f}.\n"
                f"Remaining for {month} before this payment: {month_summary['remaining']:,.0f}\n\n"
                f"Check 'Allow overpayment' if this is intentional."
            )

    return db.execute(
        """
        INSERT INTO payments (student_id, amount, payment_date, academic_year, note, received_by, month)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        (student_id, amount_value, str(payment_date).strip(), academic_year, note, received_by, month)
    )


def delete_payment(db, payment_id):
    db.execute("DELETE FROM payments WHERE id = ?;", (payment_id,))