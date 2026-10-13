"""
services/fee_structure_service.py

All database operations for fee structures. No UI code here -
ui/fees.py calls these functions instead of writing SQL directly.
"""


def get_all_fee_structures(db):
    """
    Returns all fee structures joined with class name/section for display.
    """
    query = """
        SELECT
            f.id, f.class_id, f.academic_year, f.amount,
            c.name AS class_name, c.section AS class_section
        FROM fee_structures f
        JOIN classes c ON f.class_id = c.id
        ORDER BY f.academic_year DESC, c.name, c.section;
    """
    return db.fetchall(query)


def get_fee_structure_by_id(db, fee_id: int):
    return db.fetchone("SELECT * FROM fee_structures WHERE id = ?;", (fee_id,))


def get_fee_amount(db, class_id: int, academic_year: str):
    """
    Used by the Payments module (Stage 11) to look up what a student
    in this class owes for this academic year. Returns None if no
    fee structure has been set yet.
    """
    row = db.fetchone(
        "SELECT amount FROM fee_structures WHERE class_id = ? AND academic_year = ?;",
        (class_id, academic_year)
    )
    return row["amount"] if row else None


def _fee_exists(db, class_id, academic_year, exclude_id=None):
    if exclude_id is None:
        row = db.fetchone(
            "SELECT id FROM fee_structures WHERE class_id = ? AND academic_year = ?;",
            (class_id, academic_year)
        )
    else:
        row = db.fetchone(
            "SELECT id FROM fee_structures WHERE class_id = ? AND academic_year = ? AND id != ?;",
            (class_id, academic_year, exclude_id)
        )
    return row is not None


def _validate_amount(amount):
    try:
        value = float(amount)
    except (TypeError, ValueError):
        raise ValueError("Amount must be a number.")
    if value <= 0:
        raise ValueError("Amount must be greater than zero.")
    return value


def add_fee_structure(db, class_id, academic_year, amount):
    if class_id is None:
        raise ValueError("Please select a class.")
    if not academic_year or not str(academic_year).strip():
        raise ValueError("Academic year is required.")

    academic_year = str(academic_year).strip()
    amount_value = _validate_amount(amount)

    if _fee_exists(db, class_id, academic_year):
        raise ValueError(
            "A fee already exists for this class and academic year.\n"
            "Select it from the list and edit it instead of adding a new one."
        )

    return db.execute(
        "INSERT INTO fee_structures (class_id, academic_year, amount) VALUES (?, ?, ?);",
        (class_id, academic_year, amount_value)
    )


def update_fee_structure(db, fee_id, class_id, academic_year, amount):
    if class_id is None:
        raise ValueError("Please select a class.")
    if not academic_year or not str(academic_year).strip():
        raise ValueError("Academic year is required.")

    academic_year = str(academic_year).strip()
    amount_value = _validate_amount(amount)

    if _fee_exists(db, class_id, academic_year, exclude_id=fee_id):
        raise ValueError(
            "Another fee entry already exists for this class and academic year."
        )

    db.execute(
        "UPDATE fee_structures SET class_id = ?, academic_year = ?, amount = ? WHERE id = ?;",
        (class_id, academic_year, amount_value, fee_id)
    )


def delete_fee_structure(db, fee_id):
    db.execute("DELETE FROM fee_structures WHERE id = ?;", (fee_id,))