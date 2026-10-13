"""
services/student_service.py

All database operations for students. No UI code here - ui/students.py
calls these functions instead of writing SQL directly.
"""


def get_all_students(db, search_text: str = ""):
    if search_text:
        like = f"%{search_text}%"
        query = """
            SELECT s.*, c.name AS class_name, c.section AS class_section
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            WHERE s.full_name LIKE ? OR s.father_name LIKE ? OR s.phone LIKE ?
            ORDER BY s.full_name;
        """
        return db.fetchall(query, (like, like, like))
    else:
        query = """
            SELECT s.*, c.name AS class_name, c.section AS class_section
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            ORDER BY s.full_name;
        """
        return db.fetchall(query)


def get_student_by_id(db, student_id: int):
    return db.fetchone("SELECT * FROM students WHERE id = ?;", (student_id,))


def get_students_by_class(db, class_id: int):
    """
    Used by the Class Rosters screen: every student assigned to a
    given class, regardless of active/inactive status (so the roster
    reflects reality, not just currently-active students).
    """
    return db.fetchall(
        "SELECT * FROM students WHERE class_id = ? ORDER BY full_name;",
        (class_id,)
    )


def _validate_custom_fee(custom_monthly_fee):
    """
    Blank/None means "no override, use the class's normal fee" - this
    is the default and valid. A value must be a non-negative number.
    """
    if custom_monthly_fee is None or str(custom_monthly_fee).strip() == "":
        return None
    try:
        value = float(custom_monthly_fee)
    except (TypeError, ValueError):
        raise ValueError("Custom monthly fee must be a number, or left blank.")
    if value < 0:
        raise ValueError("Custom monthly fee cannot be negative.")
    return value


def add_student(db, full_name, father_name, gender, class_id,
                 phone, address, admission_date, status, custom_monthly_fee=None):
    if not full_name or not full_name.strip():
        raise ValueError("Student name is required.")

    custom_fee_value = _validate_custom_fee(custom_monthly_fee)

    return db.execute(
        """
        INSERT INTO students
            (full_name, father_name, gender, class_id, phone, address, admission_date, status, custom_monthly_fee)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (full_name.strip(), father_name.strip() if father_name else "",
         gender, class_id, phone, address, admission_date, status, custom_fee_value)
    )


def update_student(db, student_id, full_name, father_name, gender, class_id,
                    phone, address, admission_date, status, custom_monthly_fee=None):
    if not full_name or not full_name.strip():
        raise ValueError("Student name is required.")

    custom_fee_value = _validate_custom_fee(custom_monthly_fee)

    db.execute(
        """
        UPDATE students
        SET full_name = ?, father_name = ?, gender = ?, class_id = ?,
            phone = ?, address = ?, admission_date = ?, status = ?, custom_monthly_fee = ?
        WHERE id = ?;
        """,
        (full_name.strip(), father_name.strip() if father_name else "",
         gender, class_id, phone, address, admission_date, status, custom_fee_value, student_id)
    )

def delete_student(db, student_id):
    """
    Blocks deletion if this student has any payment records - deleting
    them would otherwise silently erase financial history. To remove a
    student who has paid fees, their payment records must be deleted
    first via the Payments screen (owner only).
    """
    payment_count = db.fetchone(
        "SELECT COUNT(*) AS cnt FROM payments WHERE student_id = ?;", (student_id,)
    )
    if payment_count["cnt"] > 0:
        raise ValueError(
            f"Cannot delete this student - {payment_count['cnt']} payment record(s) exist "
            f"for them. Delete those payment records first (Payments screen - requires "
            f"the owner account) before deleting the student."
        )

    db.execute("DELETE FROM students WHERE id = ?;", (student_id,))


def get_class_options(db):
    rows = db.fetchall("SELECT id, name, section FROM classes ORDER BY name, section;")
    options = []
    for r in rows:
        label = r["name"] if not r["section"] else f"{r['name']} - {r['section']}"
        options.append((r["id"], label))
    return options


def get_student_options(db):
    rows = db.fetchall(
        "SELECT id, full_name, father_name FROM students WHERE status = 'active' ORDER BY full_name;"
    )
    options = []
    for r in rows:
        label = r["full_name"]
        if r["father_name"]:
            label = f"{r['full_name']} (پدر: {r['father_name']})"
        options.append((r["id"], label))
    return options