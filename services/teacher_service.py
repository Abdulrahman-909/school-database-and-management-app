"""
services/teacher_service.py

All database operations for teachers. No UI code here - ui/teachers.py
calls these functions instead of writing SQL directly.
"""


def get_all_teachers(db, search_text: str = ""):
    if search_text:
        like = f"%{search_text}%"
        query = """
            SELECT * FROM teachers
            WHERE full_name LIKE ? OR subject LIKE ? OR phone LIKE ?
            ORDER BY full_name;
        """
        return db.fetchall(query, (like, like, like))
    else:
        return db.fetchall("SELECT * FROM teachers ORDER BY full_name;")


def get_teacher_by_id(db, teacher_id: int):
    return db.fetchone("SELECT * FROM teachers WHERE id = ?;", (teacher_id,))


def get_teacher_options(db):
    """
    Returns a list of (teacher_id, display_label) tuples, for use by
    other modules later (e.g. Salaries in Stage 13) to populate a
    teacher dropdown - same pattern as student_service.get_class_options.
    """
    rows = db.fetchall("SELECT id, full_name FROM teachers WHERE status = 'active' ORDER BY full_name;")
    return [(r["id"], r["full_name"]) for r in rows]


def _validate_salary(salary_amount):
    try:
        value = float(salary_amount)
    except (TypeError, ValueError):
        raise ValueError("Salary must be a number.")
    if value < 0:
        raise ValueError("Salary cannot be negative.")
    return value


def add_teacher(db, full_name, phone, subject, salary_amount, status):
    if not full_name or not full_name.strip():
        raise ValueError("Teacher name is required.")

    salary_value = _validate_salary(salary_amount)

    return db.execute(
        """
        INSERT INTO teachers (full_name, phone, subject, salary_amount, status)
        VALUES (?, ?, ?, ?, ?);
        """,
        (full_name.strip(), phone, subject, salary_value, status)
    )


def update_teacher(db, teacher_id, full_name, phone, subject, salary_amount, status):
    if not full_name or not full_name.strip():
        raise ValueError("Teacher name is required.")

    salary_value = _validate_salary(salary_amount)

    db.execute(
        """
        UPDATE teachers
        SET full_name = ?, phone = ?, subject = ?, salary_amount = ?, status = ?
        WHERE id = ?;
        """,
        (full_name.strip(), phone, subject, salary_value, status, teacher_id)
    )


def delete_teacher(db, teacher_id):
    db.execute("DELETE FROM teachers WHERE id = ?;", (teacher_id,))