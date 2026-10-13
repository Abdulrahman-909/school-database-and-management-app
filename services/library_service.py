"""
services/library_service.py

All database operations for the book inventory. No UI code here -
ui/library.py calls these functions instead of writing SQL directly.

NOTE: this schema tracks total_copies / available_copies per book
title only - it does NOT track which specific student currently has
which book (that would require an additional book_transactions table,
not part of the current design). Issue/Return here just move a copy
count between "available" and "issued".
"""


def get_all_books(db, search_text: str = ""):
    if search_text:
        like = f"%{search_text}%"
        query = """
            SELECT * FROM books
            WHERE title LIKE ? OR author LIKE ?
            ORDER BY title;
        """
        return db.fetchall(query, (like, like))
    return db.fetchall("SELECT * FROM books ORDER BY title;")


def get_book_by_id(db, book_id: int):
    return db.fetchone("SELECT * FROM books WHERE id = ?;", (book_id,))


def get_total_books(db) -> int:
    row = db.fetchone("SELECT COALESCE(SUM(total_copies), 0) AS total FROM books;")
    return row["total"]


def get_total_available(db) -> int:
    row = db.fetchone("SELECT COALESCE(SUM(available_copies), 0) AS total FROM books;")
    return row["total"]


def get_total_issued(db) -> int:
    row = db.fetchone(
        "SELECT COALESCE(SUM(total_copies - available_copies), 0) AS total FROM books;"
    )
    return row["total"]


def _validate_copies(total_copies):
    try:
        value = int(total_copies)
    except (TypeError, ValueError):
        raise ValueError("Total copies must be a whole number.")
    if value < 0:
        raise ValueError("Total copies cannot be negative.")
    return value


def add_book(db, title, author, total_copies):
    if not title or not title.strip():
        raise ValueError("Book title is required.")

    total_value = _validate_copies(total_copies)

    # A brand-new book starts with all copies available.
    return db.execute(
        """
        INSERT INTO books (title, author, total_copies, available_copies, status)
        VALUES (?, ?, ?, ?, 'available');
        """,
        (title.strip(), author, total_value, total_value)
    )


def update_book(db, book_id, title, author, total_copies):
    """
    Changing total_copies adjusts available_copies by the same delta,
    so already-issued copies stay issued. Example: 10 total, 3 issued
    (7 available). Increase total to 12 -> available becomes 9
    (still 3 issued). Decrease total to 8 -> available becomes 5.
    Total cannot be reduced below the number currently issued.
    """
    if not title or not title.strip():
        raise ValueError("Book title is required.")

    new_total = _validate_copies(total_copies)

    current = get_book_by_id(db, book_id)
    if current is None:
        raise ValueError("Book not found.")

    issued = current["total_copies"] - current["available_copies"]
    if new_total < issued:
        raise ValueError(
            f"Cannot set total copies below {issued} - that many copies "
            f"are currently issued and not yet returned."
        )

    new_available = new_total - issued

    db.execute(
        """
        UPDATE books
        SET title = ?, author = ?, total_copies = ?, available_copies = ?
        WHERE id = ?;
        """,
        (title.strip(), author, new_total, new_available, book_id)
    )


def delete_book(db, book_id):
    """
    Blocks deletion if any copies are currently issued, since deleting
    would lose track of copies that are still out with students.
    """
    book = get_book_by_id(db, book_id)
    if book is None:
        raise ValueError("Book not found.")

    issued = book["total_copies"] - book["available_copies"]
    if issued > 0:
        raise ValueError(
            f"Cannot delete this book - {issued} copy/copies are still issued "
            f"and not returned. Return them first."
        )

    db.execute("DELETE FROM books WHERE id = ?;", (book_id,))


def issue_copy(db, book_id):
    """Issue one copy: available_copies -= 1. Blocked if none available."""
    book = get_book_by_id(db, book_id)
    if book is None:
        raise ValueError("Book not found.")
    if book["available_copies"] <= 0:
        raise ValueError("No copies available to issue.")

    db.execute(
        "UPDATE books SET available_copies = available_copies - 1 WHERE id = ?;",
        (book_id,)
    )


def return_copy(db, book_id):
    """Return one copy: available_copies += 1. Blocked if that would exceed total."""
    book = get_book_by_id(db, book_id)
    if book is None:
        raise ValueError("Book not found.")
    if book["available_copies"] >= book["total_copies"]:
        raise ValueError("All copies of this book are already marked as available.")

    db.execute(
        "UPDATE books SET available_copies = available_copies + 1 WHERE id = ?;",
        (book_id,)
    )