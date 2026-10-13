"""
services/course_service.py

All database operations for the Winter Courses feature: course
teachers, courses, course students, and enrollments. Deliberately
separate from student_service.py / teacher_service.py / payment_service.py -
course people and course money must never mix with the school's own
students, teachers, or payments.
"""


# ----------------------------------------------------------------------
# Course Teachers
# ----------------------------------------------------------------------

def get_all_course_teachers(db):
    return db.fetchall("SELECT * FROM course_teachers ORDER BY full_name;")


def get_course_teacher_by_id(db, teacher_id: int):
    return db.fetchone("SELECT * FROM course_teachers WHERE id = ?;", (teacher_id,))


def get_course_teacher_options(db):
    rows = db.fetchall("SELECT id, full_name FROM course_teachers ORDER BY full_name;")
    return [(r["id"], r["full_name"]) for r in rows]


def add_course_teacher(db, full_name, phone, notes):
    if not full_name or not full_name.strip():
        raise ValueError("Teacher name is required.")
    return db.execute(
        "INSERT INTO course_teachers (full_name, phone, notes) VALUES (?, ?, ?);",
        (full_name.strip(), phone, notes)
    )


def update_course_teacher(db, teacher_id, full_name, phone, notes):
    if not full_name or not full_name.strip():
        raise ValueError("Teacher name is required.")
    db.execute(
        "UPDATE course_teachers SET full_name = ?, phone = ?, notes = ? WHERE id = ?;",
        (full_name.strip(), phone, notes, teacher_id)
    )


def delete_course_teacher(db, teacher_id):
    in_use = db.fetchone("SELECT COUNT(*) AS cnt FROM courses WHERE teacher_id = ?;", (teacher_id,))
    if in_use["cnt"] > 0:
        raise ValueError(
            f"Cannot delete this teacher - {in_use['cnt']} course(s) are assigned to them. "
            f"Reassign or delete those courses first."
        )
    db.execute("DELETE FROM course_teachers WHERE id = ?;", (teacher_id,))


# ----------------------------------------------------------------------
# Courses
# ----------------------------------------------------------------------

def get_all_courses(db):
    query = """
        SELECT
            c.*,
            ct.full_name AS teacher_name,
            COALESCE((
                SELECT COUNT(*) FROM course_enrollments e WHERE e.course_id = c.id
            ), 0) AS enrolled_count
        FROM courses c
        LEFT JOIN course_teachers ct ON c.teacher_id = ct.id
        ORDER BY c.start_date DESC, c.name;
    """
    return db.fetchall(query)


def get_course_by_id(db, course_id: int):
    return db.fetchone("SELECT * FROM courses WHERE id = ?;", (course_id,))


def get_course_options(db):
    rows = db.fetchall("SELECT id, name FROM courses ORDER BY name;")
    return [(r["id"], r["name"]) for r in rows]


def _validate_percentage(percentage):
    try:
        value = float(percentage)
    except (TypeError, ValueError):
        raise ValueError("Teacher percentage must be a number.")
    if value < 0 or value > 100:
        raise ValueError("Teacher percentage must be between 0 and 100.")
    return value


def add_course(db, name, teacher_id, teacher_percentage, start_date, end_date, notes):
    if not name or not name.strip():
        raise ValueError("Course name is required.")

    percentage_value = _validate_percentage(teacher_percentage)

    return db.execute(
        """
        INSERT INTO courses (name, teacher_id, teacher_percentage, start_date, end_date, notes)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        (name.strip(), teacher_id, percentage_value, start_date, end_date, notes)
    )


def update_course(db, course_id, name, teacher_id, teacher_percentage, start_date, end_date, notes):
    if not name or not name.strip():
        raise ValueError("Course name is required.")

    percentage_value = _validate_percentage(teacher_percentage)

    db.execute(
        """
        UPDATE courses
        SET name = ?, teacher_id = ?, teacher_percentage = ?, start_date = ?, end_date = ?, notes = ?
        WHERE id = ?;
        """,
        (name.strip(), teacher_id, percentage_value, start_date, end_date, notes, course_id)
    )


def delete_course(db, course_id):
    in_use = db.fetchone(
        "SELECT COUNT(*) AS cnt FROM course_enrollments WHERE course_id = ?;", (course_id,)
    )
    if in_use["cnt"] > 0:
        raise ValueError(
            f"Cannot delete this course - {in_use['cnt']} student(s) are enrolled in it. "
            f"Remove those enrollments first."
        )
    db.execute("DELETE FROM courses WHERE id = ?;", (course_id,))


# ----------------------------------------------------------------------
# Course Students
# ----------------------------------------------------------------------

def get_all_course_students(db, search_text: str = ""):
    if search_text:
        like = f"%{search_text}%"
        return db.fetchall(
            "SELECT * FROM course_students WHERE full_name LIKE ? OR phone LIKE ? ORDER BY full_name;",
            (like, like)
        )
    return db.fetchall("SELECT * FROM course_students ORDER BY full_name;")


def get_course_student_by_id(db, student_id: int):
    return db.fetchone("SELECT * FROM course_students WHERE id = ?;", (student_id,))


def get_course_student_options(db):
    rows = db.fetchall("SELECT id, full_name, phone FROM course_students ORDER BY full_name;")
    options = []
    for r in rows:
        label = r["full_name"]
        if r["phone"]:
            label = f"{r['full_name']} ({r['phone']})"
        options.append((r["id"], label))
    return options


def add_course_student(db, full_name, phone, notes):
    if not full_name or not full_name.strip():
        raise ValueError("Student name is required.")
    return db.execute(
        "INSERT INTO course_students (full_name, phone, notes) VALUES (?, ?, ?);",
        (full_name.strip(), phone, notes)
    )


def update_course_student(db, student_id, full_name, phone, notes):
    if not full_name or not full_name.strip():
        raise ValueError("Student name is required.")
    db.execute(
        "UPDATE course_students SET full_name = ?, phone = ?, notes = ? WHERE id = ?;",
        (full_name.strip(), phone, notes, student_id)
    )


def delete_course_student(db, student_id):
    in_use = db.fetchone(
        "SELECT COUNT(*) AS cnt FROM course_enrollments WHERE course_student_id = ?;", (student_id,)
    )
    if in_use["cnt"] > 0:
        raise ValueError(
            f"Cannot delete this student - they are enrolled in {in_use['cnt']} course(s). "
            f"Remove those enrollments first."
        )
    db.execute("DELETE FROM course_students WHERE id = ?;", (student_id,))


# ----------------------------------------------------------------------
# Enrollments (course + student + THIS student's individual fee)
# ----------------------------------------------------------------------

def get_all_enrollments(db, course_id: int = None):
    if course_id:
        query = """
            SELECT e.*, c.name AS course_name, cs.full_name AS student_name, cs.phone AS student_phone
            FROM course_enrollments e
            JOIN courses c ON e.course_id = c.id
            JOIN course_students cs ON e.course_student_id = cs.id
            WHERE e.course_id = ?
            ORDER BY cs.full_name;
        """
        return db.fetchall(query, (course_id,))

    query = """
        SELECT e.*, c.name AS course_name, cs.full_name AS student_name, cs.phone AS student_phone
        FROM course_enrollments e
        JOIN courses c ON e.course_id = c.id
        JOIN course_students cs ON e.course_student_id = cs.id
        ORDER BY e.enrollment_date DESC, e.id DESC;
    """
    return db.fetchall(query)


def get_enrollment_by_id(db, enrollment_id: int):
    return db.fetchone("SELECT * FROM course_enrollments WHERE id = ?;", (enrollment_id,))


def _validate_fee(fee_amount):
    try:
        value = float(fee_amount)
    except (TypeError, ValueError):
        raise ValueError("Fee amount must be a number.")
    if value <= 0:
        raise ValueError("Fee amount must be greater than zero.")
    return value


def _already_enrolled(db, course_id, course_student_id, exclude_id=None):
    if exclude_id is None:
        row = db.fetchone(
            "SELECT id FROM course_enrollments WHERE course_id = ? AND course_student_id = ?;",
            (course_id, course_student_id)
        )
    else:
        row = db.fetchone(
            "SELECT id FROM course_enrollments WHERE course_id = ? AND course_student_id = ? AND id != ?;",
            (course_id, course_student_id, exclude_id)
        )
    return row is not None


def add_enrollment(db, course_id, course_student_id, fee_amount, enrollment_date):
    if course_id is None:
        raise ValueError("Please select a course.")
    if course_student_id is None:
        raise ValueError("Please select a student.")

    fee_value = _validate_fee(fee_amount)

    if _already_enrolled(db, course_id, course_student_id):
        raise ValueError("This student is already enrolled in this course.")

    return db.execute(
        """
        INSERT INTO course_enrollments (course_id, course_student_id, fee_amount, enrollment_date)
        VALUES (?, ?, ?, ?);
        """,
        (course_id, course_student_id, fee_value, enrollment_date)
    )


def update_enrollment(db, enrollment_id, course_id, course_student_id, fee_amount, enrollment_date):
    if course_id is None:
        raise ValueError("Please select a course.")
    if course_student_id is None:
        raise ValueError("Please select a student.")

    fee_value = _validate_fee(fee_amount)

    if _already_enrolled(db, course_id, course_student_id, exclude_id=enrollment_id):
        raise ValueError("This student is already enrolled in this course.")

    db.execute(
        """
        UPDATE course_enrollments
        SET course_id = ?, course_student_id = ?, fee_amount = ?, enrollment_date = ?
        WHERE id = ?;
        """,
        (course_id, course_student_id, fee_value, enrollment_date, enrollment_id)
    )


def delete_enrollment(db, enrollment_id):
    """
    Blocks deletion if the student has already made payments against
    this enrollment - deleting it would silently erase their payment
    history (and orphan the course_payments rows, which is what
    caused the raw FOREIGN KEY error). The user must delete those
    payments first (Course Details tab), which is itself owner-only,
    so removing a paid enrollment is a deliberate two-step action.
    """
    payment_count = db.fetchone(
        "SELECT COUNT(*) AS cnt FROM course_payments WHERE enrollment_id = ?;", (enrollment_id,)
    )
    if payment_count["cnt"] > 0:
        raise ValueError(
            f"Cannot remove this enrollment - {payment_count['cnt']} payment(s) have already been "
            f"recorded against it. Go to the 'Course Details' tab and delete those payments first "
            f"(this requires the owner account)."
        )

    db.execute("DELETE FROM course_enrollments WHERE id = ?;", (enrollment_id,))