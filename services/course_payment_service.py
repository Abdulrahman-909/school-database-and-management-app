"""
services/course_payment_service.py

Student payments per course enrollment, and teacher revenue-share
tracking for Winter Courses. Built on top of course_service.py (Stage
21a) - imports it for enrollment/course lookups rather than duplicating
those queries.

Key rule: the teacher's share is ALWAYS calculated from money actually
COLLECTED from students (sum of course_payments), never from the sum
of enrollment fee_amounts (which is only what's owed, not received).
This mirrors the same "never trust an unpaid promise as real income"
principle used throughout the rest of the app.
"""

from services import course_service


# ----------------------------------------------------------------------
# Student payments (per enrollment)
# ----------------------------------------------------------------------

def get_enrollment_summary(db, enrollment_id: int):
    """
    Returns a dict with the enrollment's fee, total paid, and remaining -
    same Total/Paid/Remaining pattern as the school's payment_service.
    """
    enrollment = course_service.get_enrollment_by_id(db, enrollment_id)
    if enrollment is None:
        raise ValueError("Enrollment not found.")

    total_paid = get_total_paid_for_enrollment(db, enrollment_id)
    remaining = enrollment["fee_amount"] - total_paid

    return {
        "enrollment": enrollment,
        "total_fee": enrollment["fee_amount"],
        "total_paid": total_paid,
        "remaining": remaining,
    }


def get_total_paid_for_enrollment(db, enrollment_id: int) -> float:
    row = db.fetchone(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM course_payments WHERE enrollment_id = ?;",
        (enrollment_id,)
    )
    return row["total"]


def get_payments_for_enrollment(db, enrollment_id: int):
    return db.fetchall(
        "SELECT * FROM course_payments WHERE enrollment_id = ? ORDER BY payment_date DESC, id DESC;",
        (enrollment_id,)
    )


def _validate_amount(amount):
    try:
        value = float(amount)
    except (TypeError, ValueError):
        raise ValueError("Amount must be a number.")
    if value <= 0:
        raise ValueError("Amount must be greater than zero.")
    return value


def add_course_payment(db, enrollment_id, amount, payment_date, note, allow_overpayment=False):
    if enrollment_id is None:
        raise ValueError("Please select an enrollment.")
    if not payment_date or not str(payment_date).strip():
        raise ValueError("Payment date is required.")

    amount_value = _validate_amount(amount)

    summary = get_enrollment_summary(db, enrollment_id)
    if not allow_overpayment:
        new_total = summary["total_paid"] + amount_value
        if new_total > summary["total_fee"]:
            over_by = new_total - summary["total_fee"]
            raise ValueError(
                f"This payment would exceed the remaining fee by {over_by:,.0f}.\n"
                f"Remaining before this payment: {summary['remaining']:,.0f}\n\n"
                f"Check 'Allow overpayment' if this is intentional."
            )

    return db.execute(
        "INSERT INTO course_payments (enrollment_id, amount, payment_date, note) VALUES (?, ?, ?, ?);",
        (enrollment_id, amount_value, str(payment_date).strip(), note)
    )


def delete_course_payment(db, payment_id):
    db.execute("DELETE FROM course_payments WHERE id = ?;", (payment_id,))


# ----------------------------------------------------------------------
# Course-level totals and teacher share
# ----------------------------------------------------------------------

def get_total_collected_for_course(db, course_id: int) -> float:
    """
    Sum of ALL course_payments across ALL enrollments in this course -
    money actually received, not money owed.
    """
    row = db.fetchone(
        """
        SELECT COALESCE(SUM(cp.amount), 0) AS total
        FROM course_payments cp
        JOIN course_enrollments ce ON cp.enrollment_id = ce.id
        WHERE ce.course_id = ?;
        """,
        (course_id,)
    )
    return row["total"]


def get_total_teacher_payouts(db, course_id: int) -> float:
    row = db.fetchone(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM course_teacher_payments WHERE course_id = ?;",
        (course_id,)
    )
    return row["total"]


def get_course_financial_summary(db, course_id: int):
    """
    Returns everything needed for the Course Details screen:
    total collected from students, the teacher's calculated share
    (owed), how much of that share has actually been paid out, and
    what's still owed to the teacher.
    """
    course = course_service.get_course_by_id(db, course_id)
    if course is None:
        raise ValueError("Course not found.")

    total_collected = get_total_collected_for_course(db, course_id)
    teacher_owed = total_collected * (course["teacher_percentage"] / 100)
    teacher_paid = get_total_teacher_payouts(db, course_id)
    teacher_remaining = teacher_owed - teacher_paid
    school_share = total_collected - teacher_owed

    return {
        "course": course,
        "total_collected": total_collected,
        "teacher_owed": teacher_owed,
        "teacher_paid": teacher_paid,
        "teacher_remaining": teacher_remaining,
        "school_share": school_share,
    }


def get_teacher_payouts(db, course_id: int):
    return db.fetchall(
        "SELECT * FROM course_teacher_payments WHERE course_id = ? ORDER BY payment_date DESC, id DESC;",
        (course_id,)
    )


def add_teacher_payout(db, course_id, amount, payment_date, note, allow_overpayment=False):
    if course_id is None:
        raise ValueError("Please select a course.")
    if not payment_date or not str(payment_date).strip():
        raise ValueError("Payment date is required.")

    amount_value = _validate_amount(amount)

    summary = get_course_financial_summary(db, course_id)
    if not allow_overpayment:
        new_total = summary["teacher_paid"] + amount_value
        if new_total > summary["teacher_owed"]:
            over_by = new_total - summary["teacher_owed"]
            raise ValueError(
                f"This payout would exceed what's owed to the teacher by {over_by:,.0f}.\n"
                f"Remaining owed before this payout: {summary['teacher_remaining']:,.0f}\n\n"
                f"Check 'Allow overpayment' if this is intentional."
            )

    return db.execute(
        "INSERT INTO course_teacher_payments (course_id, amount, payment_date, note) VALUES (?, ?, ?, ?);",
        (course_id, amount_value, str(payment_date).strip(), note)
    )


def delete_teacher_payout(db, payout_id):
    db.execute("DELETE FROM course_teacher_payments WHERE id = ?;", (payout_id,))