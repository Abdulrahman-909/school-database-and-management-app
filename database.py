"""
database.py

Owns the single SQLite connection for the School Management app.
Every other module (services, ui) should go through this class to
touch the database - nobody should call sqlite3.connect() directly
anywhere else in the project.
"""

import sqlite3
import os
from pathlib import Path


class DatabaseError(Exception):
    """Raised when a database operation fails, with a clear message."""
    pass


class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            project_root = Path(__file__).resolve().parent.parent
            data_folder = project_root / "data"
            data_folder.mkdir(exist_ok=True)
            db_path = str(data_folder / "school_app.db")

        self.db_path = db_path
        self._connect()
        self.create_tables()

    def _connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON;")
        except sqlite3.Error as e:
            raise DatabaseError(f"Could not open database at {self.db_path}: {e}")

    # ------------------------------------------------------------------
    # Core helpers - all other code should use these, not raw sqlite3
    # ------------------------------------------------------------------

    def execute(self, query: str, params: tuple = ()):
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"[DATABASE ERROR] Query failed: {query} | params={params} | {e}")
            raise DatabaseError(str(e))

    def fetchone(self, query: str, params: tuple = ()):
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            return cur.fetchone()
        except sqlite3.Error as e:
            print(f"[DATABASE ERROR] Query failed: {query} | params={params} | {e}")
            raise DatabaseError(str(e))

    def fetchall(self, query: str, params: tuple = ()):
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            return cur.fetchall()
        except sqlite3.Error as e:
            print(f"[DATABASE ERROR] Query failed: {query} | params={params} | {e}")
            raise DatabaseError(str(e))

    def close(self):
        if self.conn:
            self.conn.close()

    # ------------------------------------------------------------------
    # Backup / Restore
    # ------------------------------------------------------------------

    def backup_to(self, destination_path: str):
        try:
            dest_conn = sqlite3.connect(destination_path)
            with dest_conn:
                self.conn.backup(dest_conn)
            dest_conn.close()
        except sqlite3.Error as e:
            raise DatabaseError(f"Backup failed: {e}")

    def restore_from(self, source_path: str):
        if not os.path.exists(source_path):
            raise DatabaseError(f"Backup file not found: {source_path}")

        try:
            self.close()

            source_conn = sqlite3.connect(source_path)
            dest_conn = sqlite3.connect(self.db_path)
            with dest_conn:
                source_conn.backup(dest_conn)
            source_conn.close()
            dest_conn.close()
        except sqlite3.Error as e:
            self._connect()
            raise DatabaseError(f"Restore failed: {e}")

        self._connect()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'admin',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                section TEXT,
                capacity INTEGER DEFAULT 30
            );

            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                father_name TEXT,
                gender TEXT,
                class_id INTEGER,
                phone TEXT,
                address TEXT,
                admission_date TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY (class_id) REFERENCES classes (id)
            );

            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                phone TEXT,
                subject TEXT,
                salary_amount REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS fee_structures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                academic_year TEXT NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY (class_id) REFERENCES classes (id)
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_date TEXT NOT NULL,
                academic_year TEXT,
                note TEXT,
                received_by TEXT,
                FOREIGN KEY (student_id) REFERENCES students (id)
            );

            CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                amount REAL NOT NULL,
                income_date TEXT NOT NULL,
                note TEXT
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                amount REAL NOT NULL,
                expense_date TEXT NOT NULL,
                note TEXT
            );

            CREATE TABLE IF NOT EXISTS salaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_date TEXT NOT NULL,
                month TEXT,
                note TEXT,
                FOREIGN KEY (teacher_id) REFERENCES teachers (id)
            );

            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT,
                total_copies INTEGER NOT NULL DEFAULT 1,
                available_copies INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'available'
            );

            -- ============================================================
            -- WINTER COURSES - completely separate from the school's own
            -- students/teachers/payments tables on purpose.
            -- ============================================================

            CREATE TABLE IF NOT EXISTS course_teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                phone TEXT,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                teacher_id INTEGER,
                teacher_percentage REAL NOT NULL DEFAULT 0,
                start_date TEXT,
                end_date TEXT,
                notes TEXT,
                FOREIGN KEY (teacher_id) REFERENCES course_teachers (id)
            );

            CREATE TABLE IF NOT EXISTS course_students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                phone TEXT,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS course_enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                course_student_id INTEGER NOT NULL,
                fee_amount REAL NOT NULL,
                enrollment_date TEXT,
                FOREIGN KEY (course_id) REFERENCES courses (id),
                FOREIGN KEY (course_student_id) REFERENCES course_students (id)
            );

            CREATE TABLE IF NOT EXISTS course_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enrollment_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_date TEXT NOT NULL,
                note TEXT,
                FOREIGN KEY (enrollment_id) REFERENCES course_enrollments (id)
            );

            CREATE TABLE IF NOT EXISTS course_teacher_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_date TEXT NOT NULL,
                note TEXT,
                FOREIGN KEY (course_id) REFERENCES courses (id)
            );
        """)
        self._migrate_add_payment_month_column()
        self._migrate_add_custom_monthly_fee_column()
        self.conn.commit()

    def _migrate_add_payment_month_column(self):
        """
        Adds the 'month' column to the (school) payments table if it
        doesn't already exist. Safe to run every startup - on a brand
        new database CREATE TABLE above already includes nothing about
        month, so this always runs once; on an existing database missing
        the column, this adds it without touching existing rows (their
        month will just be NULL/empty until re-entered).
        """
        try:
            self.conn.execute("ALTER TABLE payments ADD COLUMN month TEXT;")
        except sqlite3.OperationalError:
            pass  # column already exists

    def _migrate_add_custom_monthly_fee_column(self):
        """
        Adds 'custom_monthly_fee' to students - NULL/blank means the
        student uses their class's normal monthly fee (unchanged
        behavior). A number here overrides the class fee for THIS
        student only (e.g. poverty discount, sibling discount).
        """
        try:
            self.conn.execute("ALTER TABLE students ADD COLUMN custom_monthly_fee REAL;")
        except sqlite3.OperationalError:
            pass  # column already exists


# ----------------------------------------------------------------------
# Quick manual test
# ----------------------------------------------------------------------
if __name__ == "__main__":
    db = Database()
    print(f"Database opened at: {db.db_path}")

    tables = db.fetchall("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    print("\nTables:")
    for row in tables:
        print(" -", row["name"])

    cols = db.fetchall("PRAGMA table_info(payments);")
    print("\nColumns in 'payments':")
    for c in cols:
        print(f"  {c['name']} ({c['type']})")

    db.close()
    print("\nConnection closed. Test complete.")