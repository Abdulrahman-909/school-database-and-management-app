"""
ui/rosters.py

Class Rosters module: read-only viewer. Pick a school class or a
winter course from a list, see everyone enrolled in it. No add/edit/
delete here - all of that lives in Classes, Students, and Winter
Courses already; this screen is purely for quickly looking someone up.
"""

import tkinter as tk
from tkinter import ttk

from services import class_service
from services import student_service
from services import course_service
from services import course_payment_service


class RostersFrame(ttk.Frame):
    def __init__(self, parent, db, on_back):
        super().__init__(parent, padding=15)
        self.db = db
        self.on_back = on_back

        self.pack(fill="both", expand=True)

        self._build_header()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, pady=(10, 0))

        self.school_tab = SchoolRosterTab(notebook, db)
        self.course_tab = CourseRosterTab(notebook, db)

        notebook.add(
            self.school_tab,
            text="صنوف مکتب / School Classes"
        )

        notebook.add(
            self.course_tab,
            text="دوره‌های زمستانی / Winter Courses"
        )

    def _build_header(self):
        header = ttk.Frame(self)
        header.pack(fill="x")

        ttk.Button(
            header,
            text="< بازگشت / Back",
            command=self.on_back
        ).pack(side="left")

        ttk.Label(
            header,
            text="لیست صنوف / Class Rosters",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=15)


class SchoolRosterTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, padding=10)
        self.db = db

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)

        ttk.Label(
            self,
            text="صنوف / Classes",
            font=("Segoe UI", 10, "bold")
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 5)
        )

        ttk.Label(
            self,
            text="شاگردان این صنف / Students in This Class",
            font=("Segoe UI", 10, "bold")
        ).grid(
            row=0,
            column=1,
            sticky="w",
            pady=(0, 5)
        )

        # --------------------------------------------------------------
        # SCHOOL CLASSES LIST
        # --------------------------------------------------------------

        class_list_frame = ttk.Frame(self)

        class_list_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(0, 10)
        )

        class_columns = (
            "id",
            "name",
            "count"
        )

        self.class_tree = ttk.Treeview(
            class_list_frame,
            columns=class_columns,
            show="headings",
            height=20
        )

        self.class_tree.heading(
            "id",
            text="ID"
        )

        self.class_tree.heading(
            "name",
            text="صنف / Class"
        )

        self.class_tree.heading(
            "count",
            text="شاگردان / Students"
        )

        self.class_tree.column(
            "id",
            width=50,
            anchor="center"
        )

        self.class_tree.column(
            "name",
            width=180,
            anchor="center"
        )

        self.class_tree.column(
            "count",
            width=100,
            anchor="center"
        )

        self.class_tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        class_scrollbar = ttk.Scrollbar(
            class_list_frame,
            orient="vertical",
            command=self.class_tree.yview
        )

        class_scrollbar.pack(
            side="right",
            fill="y"
        )

        self.class_tree.configure(
            yscrollcommand=class_scrollbar.set
        )

        self.class_tree.bind(
            "<<TreeviewSelect>>",
            self._handle_class_select
        )

        # --------------------------------------------------------------
        # SCHOOL STUDENTS LIST
        # --------------------------------------------------------------

        student_list_frame = ttk.Frame(self)

        student_list_frame.grid(
            row=1,
            column=1,
            sticky="nsew"
        )

        student_columns = (
            "name",
            "father",
            "phone",
            "status"
        )

        self.student_tree = ttk.Treeview(
            student_list_frame,
            columns=student_columns,
            show="headings",
            height=20
        )

        headings = {
            "name": "نام / Name",
            "father": "نام پدر / Father",
            "phone": "تلفن / Phone",
            "status": "وضعیت / Status"
        }

        widths = {
            "name": 180,
            "father": 150,
            "phone": 120,
            "status": 100
        }

        for col in student_columns:
            self.student_tree.heading(
                col,
                text=headings[col]
            )

            self.student_tree.column(
                col,
                width=widths[col],
                anchor="center"
            )

        self.student_tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        student_scrollbar = ttk.Scrollbar(
            student_list_frame,
            orient="vertical",
            command=self.student_tree.yview
        )

        student_scrollbar.pack(
            side="right",
            fill="y"
        )

        self.student_tree.configure(
            yscrollcommand=student_scrollbar.set
        )

        # --------------------------------------------------------------
        # REFRESH
        # --------------------------------------------------------------

        ttk.Button(
            self,
            text="تازه‌سازی / Refresh",
            command=self.refresh_classes
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=(10, 0)
        )

        self.refresh_classes()

    def refresh_classes(self):
        for row in self.class_tree.get_children():
            self.class_tree.delete(row)

        for row in self.student_tree.get_children():
            self.student_tree.delete(row)

        for c in class_service.get_all_classes(self.db):
            label = (
                c["name"]
                if not c["section"]
                else f"{c['name']} - {c['section']}"
            )

            self.class_tree.insert(
                "",
                "end",
                values=(
                    c["id"],
                    label,
                    c["current_students"]
                )
            )

    def _handle_class_select(self, event):
        selection = self.class_tree.selection()

        if not selection:
            return

        item = self.class_tree.item(selection[0])
        class_id = item["values"][0]

        for row in self.student_tree.get_children():
            self.student_tree.delete(row)

        for s in student_service.get_students_by_class(
            self.db,
            class_id
        ):
            self.student_tree.insert(
                "",
                "end",
                values=(
                    s["full_name"],
                    s["father_name"] or "",
                    s["phone"] or "",
                    s["status"]
                )
            )


class CourseRosterTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, padding=10)
        self.db = db

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)

        ttk.Label(
            self,
            text="دوره‌ها / Courses",
            font=("Segoe UI", 10, "bold")
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 5)
        )

        ttk.Label(
            self,
            text="شاگردان این دوره / Students in This Course",
            font=("Segoe UI", 10, "bold")
        ).grid(
            row=0,
            column=1,
            sticky="w",
            pady=(0, 5)
        )

        # --------------------------------------------------------------
        # WINTER COURSES LIST
        # --------------------------------------------------------------

        course_list_frame = ttk.Frame(self)

        course_list_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(0, 10)
        )

        course_columns = (
            "id",
            "name",
            "teacher",
            "count"
        )

        self.course_tree = ttk.Treeview(
            course_list_frame,
            columns=course_columns,
            show="headings",
            height=20
        )

        self.course_tree.heading(
            "id",
            text="ID"
        )

        self.course_tree.heading(
            "name",
            text="دوره / Course"
        )

        self.course_tree.heading(
            "teacher",
            text="استاد / Teacher"
        )

        self.course_tree.heading(
            "count",
            text="شاگردان / Students"
        )

        self.course_tree.column(
            "id",
            width=40,
            anchor="center"
        )

        self.course_tree.column(
            "name",
            width=140,
            anchor="center"
        )

        self.course_tree.column(
            "teacher",
            width=120,
            anchor="center"
        )

        self.course_tree.column(
            "count",
            width=90,
            anchor="center"
        )

        self.course_tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        course_scrollbar = ttk.Scrollbar(
            course_list_frame,
            orient="vertical",
            command=self.course_tree.yview
        )

        course_scrollbar.pack(
            side="right",
            fill="y"
        )

        self.course_tree.configure(
            yscrollcommand=course_scrollbar.set
        )

        self.course_tree.bind(
            "<<TreeviewSelect>>",
            self._handle_course_select
        )

        # --------------------------------------------------------------
        # COURSE STUDENTS LIST
        # --------------------------------------------------------------

        student_list_frame = ttk.Frame(self)

        student_list_frame.grid(
            row=1,
            column=1,
            sticky="nsew"
        )

        student_columns = (
            "name",
            "phone",
            "fee",
            "paid",
            "remaining"
        )

        self.student_tree = ttk.Treeview(
            student_list_frame,
            columns=student_columns,
            show="headings",
            height=20
        )

        headings = {
            "name": "نام / Name",
            "phone": "تلفن / Phone",
            "fee": "فیس / Fee",
            "paid": "پرداخت شده / Paid",
            "remaining": "باقی مانده / Remaining"
        }

        widths = {
            "name": 150,
            "phone": 110,
            "fee": 90,
            "paid": 100,
            "remaining": 100
        }

        for col in student_columns:
            self.student_tree.heading(
                col,
                text=headings[col]
            )

            self.student_tree.column(
                col,
                width=widths[col],
                anchor="center"
            )

        self.student_tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        course_student_scrollbar = ttk.Scrollbar(
            student_list_frame,
            orient="vertical",
            command=self.student_tree.yview
        )

        course_student_scrollbar.pack(
            side="right",
            fill="y"
        )

        self.student_tree.configure(
            yscrollcommand=course_student_scrollbar.set
        )

        # --------------------------------------------------------------
        # REFRESH
        # --------------------------------------------------------------

        ttk.Button(
            self,
            text="تازه‌سازی / Refresh",
            command=self.refresh_courses
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=(10, 0)
        )

        self.refresh_courses()

    def refresh_courses(self):
        for row in self.course_tree.get_children():
            self.course_tree.delete(row)

        for row in self.student_tree.get_children():
            self.student_tree.delete(row)

        for c in course_service.get_all_courses(self.db):
            self.course_tree.insert(
                "",
                "end",
                values=(
                    c["id"],
                    c["name"],
                    c["teacher_name"] or "-",
                    c["enrolled_count"]
                )
            )

    def _handle_course_select(self, event):
        selection = self.course_tree.selection()

        if not selection:
            return

        item = self.course_tree.item(selection[0])
        course_id = item["values"][0]

        for row in self.student_tree.get_children():
            self.student_tree.delete(row)

        for e in course_service.get_all_enrollments(
            self.db,
            course_id
        ):
            summary = course_payment_service.get_enrollment_summary(
                self.db,
                e["id"]
            )

            self.student_tree.insert(
                "",
                "end",
                values=(
                    e["student_name"],
                    e["student_phone"] or "",
                    f"{summary['total_fee']:,.0f}",
                    f"{summary['total_paid']:,.0f}",
                    f"{summary['remaining']:,.0f}"
                )
            )