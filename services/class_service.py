"""
services/class_service.py

All database operations for classes. No UI code here - ui/classes.py
calls these functions instead of writing SQL directly.
"""


def get_all_classes(db):
    """
    Returns all classes with a LIVE count of currently-assigned students
    (status = 'active') and the resulting available seats. These are
    calculated every call, not stored, so they're always accurate.
    """
    query = """
        SELECT
            c.id,
            c.name,
            c.section,
            c.capacity,
            COALESCE((
                SELECT COUNT(*) FROM students s
                WHERE s.class_id = c.id AND s.status = 'active'
            ), 0) AS current_students
        FROM classes c
        ORDER BY c.name, c.section;
    """
    rows = db.fetchall(query)

    result = []
    for r in rows:
        row_dict = dict(r)
        row_dict["available_seats"] = row_dict["capacity"] - row_dict["current_students"]
        result.append(row_dict)
    return result


def get_class_by_id(db, class_id: int):
    return db.fetchone("SELECT * FROM classes WHERE id = ?;", (class_id,))


def get_class_options(db):
    """
    Returns a list of (class_id, display_label) tuples for populating
    class dropdowns anywhere in the app (Students, Fee Structure,
    Payments, etc.) - the single shared source for this list.
    """
    rows = db.fetchall("SELECT id, name, section FROM classes ORDER BY name, section;")
    options = []
    for r in rows:
        label = r["name"] if not r["section"] else f"{r['name']} - {r['section']}"
        options.append((r["id"], label))
    return options


def get_student_count_for_class(db, class_id: int) -> int:
    row = db.fetchone(
        "SELECT COUNT(*) AS cnt FROM students WHERE class_id = ?;", (class_id,)
    )
    return row["cnt"]


def _validate_capacity(capacity):
    try:
        value = int(capacity)
    except (TypeError, ValueError):
        raise ValueError("Capacity must be a whole number.")
    if value <= 0:
        raise ValueError("Capacity must be greater than zero.")
    return value


def add_class(db, name, section, capacity):
    if not name or not name.strip():
        raise ValueError("Class name is required.")

    capacity_value = _validate_capacity(capacity)

    return db.execute(
        "INSERT INTO classes (name, section, capacity) VALUES (?, ?, ?);",
        (name.strip(), section.strip() if section else "", capacity_value)
    )


def update_class(db, class_id, name, section, capacity):
    if not name or not name.strip():
        raise ValueError("Class name is required.")

    capacity_value = _validate_capacity(capacity)

    db.execute(
        "UPDATE classes SET name = ?, section = ?, capacity = ? WHERE id = ?;",
        (name.strip(), section.strip() if section else "", capacity_value, class_id)
    )


def delete_class(db, class_id):
    """
    Blocks deletion if students are still assigned to this class,
    instead of leaving orphaned class_id references behind.
    """
    student_count = get_student_count_for_class(db, class_id)
    if student_count > 0:
        raise ValueError(
            f"Cannot delete this class - {student_count} student(s) are still "
            f"assigned to it. Reassign or remove them first."
        )

    db.execute("DELETE FROM classes WHERE id = ?;", (class_id,))