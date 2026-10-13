"""
ui/reports.py

Reports module: read-only summaries pulled from the already-tested
services. No editing here - this screen only displays data; changes
happen in the individual module screens.
"""

import tkinter as tk
from tkinter import ttk
from datetime import date

from services import student_service
from services import payment_service
from services import finance_service
from services import salary_service
from services import library_service
from services import class_service


class ReportsFrame(ttk.Frame):
    def __init__(self, parent, db, on_back):
        super().__init__(parent, padding=15)
        self.db = db
        self.on_back = on_back

        self.pack(fill="both", expand=True)

        self._build_header()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, pady=(10, 0))

        self.students_tab = StudentsReportTab(notebook, db)
        self.fees_tab = FeesReportTab(notebook, db)
        self.financial_tab = FinancialReportTab(notebook, db)
        self.salaries_tab = SalariesReportTab(notebook, db)
        self.library_tab = LibraryReportTab(notebook, db)

        notebook.add(self.students_tab, text="شاگردان / Students")
        notebook.add(self.fees_tab, text="فیس / Fees")
        notebook.add(self.financial_tab, text="مالی / Financial Summary")
        notebook.add(self.salaries_tab, text="معاشات / Salaries")
        notebook.add(self.library_tab, text="کتابخانه / Library")

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
            text="گزارش‌ها / Reports",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=15)


# ==========================================================================
# Students report
# ==========================================================================

class StudentsReportTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, padding=15)
        self.db = db

        self.summary_label = ttk.Label(
            self,
            text="",
            font=("Segoe UI", 10),
            justify="left"
        )
        self.summary_label.pack(anchor="w", pady=(0, 15))

        ttk.Label(
            self,
            text="تفکیک بر اساس صنف / Breakdown by Class",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 5))

        columns = ("class", "current", "capacity", "available")

        # Container for list + scrollbar
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=10
        )

        headings = {
            "class": "صنف / Class",
            "current": "شاگردان / Students",
            "capacity": "ظرفیت / Capacity",
            "available": "جای خالی / Available",
        }

        widths = {
            "class": 200,
            "current": 130,
            "capacity": 130,
            "available": 130
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")

        # Scrollbar for the list only
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        ttk.Button(
            self,
            text="تازه‌سازی / Refresh",
            command=self.refresh
        ).pack(anchor="w", pady=(10, 0))

        self.refresh()

    def refresh(self):
        all_students = student_service.get_all_students(self.db)

        total = len(all_students)

        male = sum(
            1 for s in all_students
            if s["gender"] and "Male" in s["gender"]
            or s["gender"] == "ذکور"
        )

        female = sum(
            1 for s in all_students
            if s["gender"] and "Female" in s["gender"]
            or s["gender"] == "اناث"
        )

        active = sum(
            1 for s in all_students
            if s["status"] == "active"
        )

        inactive = total - active

        self.summary_label.config(
            text=(
                f"مجموع شاگردان / Total Students: {total}\n"
                f"شاگردان ذکور / Male: {male}      "
                f"شاگردان اناث / Female: {female}\n"
                f"فعال / Active: {active}      "
                f"غیر فعال / Inactive: {inactive}"
            )
        )

        for row in self.tree.get_children():
            self.tree.delete(row)

        for c in class_service.get_all_classes(self.db):
            label = (
                c["name"]
                if not c["section"]
                else f"{c['name']} - {c['section']}"
            )

            self.tree.insert(
                "",
                "end",
                values=(
                    label,
                    c["current_students"],
                    c["capacity"],
                    c["available_seats"]
                )
            )


# ==========================================================================
# Fees report
# ==========================================================================

class FeesReportTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, padding=15)
        self.db = db

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 10))

        ttk.Label(
            top,
            text="سال تعلیمی / Academic Year:"
        ).pack(side="left", padx=(0, 5))

        self.year_var = tk.StringVar(
            value=str(date.today().year)
        )

        ttk.Entry(
            top,
            textvariable=self.year_var,
            width=15
        ).pack(side="left", padx=5)

        ttk.Button(
            top,
            text="نمایش / Show",
            command=self.refresh
        ).pack(side="left", padx=10)

        self.summary_label = ttk.Label(
            self,
            text="",
            font=("Segoe UI", 10)
        )
        self.summary_label.pack(
            anchor="w",
            pady=(0, 10)
        )

        ttk.Label(
            self,
            text="شاگردانی که فیس باقی‌مانده دارند / Students With Remaining Fees",
            font=("Segoe UI", 11, "bold")
        ).pack(
            anchor="w",
            pady=(5, 5)
        )

        columns = (
            "name",
            "class",
            "total_fee",
            "paid",
            "remaining"
        )

        # Container for list + scrollbar
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=12
        )

        headings = {
            "name": "نام / Name",
            "class": "صنف / Class",
            "total_fee": "قابل پرداخت / Total Fee",
            "paid": "پرداخت شده / Paid",
            "remaining": "باقی مانده / Remaining",
        }

        widths = {
            "name": 180,
            "class": 150,
            "total_fee": 120,
            "paid": 120,
            "remaining": 120
        }

        for col in columns:
            self.tree.heading(
                col,
                text=headings[col]
            )
            self.tree.column(
                col,
                width=widths[col],
                anchor="center"
            )

        self.tree.tag_configure(
            "owes",
            background="#f8d7da"
        )

        # Scrollbar for the list only
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.refresh()

    def refresh(self):
        year = self.year_var.get().strip()

        if not year:
            return

        total_collected = payment_service.get_total_paid_all_students(
            self.db
        )

        remaining_list = payment_service.get_students_with_remaining_fees(
            self.db,
            year
        )

        total_remaining = sum(
            s["remaining"]
            for s in remaining_list
        )

        self.summary_label.config(
            text=(
                f"مجموع فیس دریافت شده (همه سال‌ها) / "
                f"Total Fees Collected (all years): "
                f"{total_collected:,.0f}\n"
                f"مجموع باقی‌مانده برای سال {year} / "
                f"Total Remaining for {year}: "
                f"{total_remaining:,.0f}"
            )
        )

        for row in self.tree.get_children():
            self.tree.delete(row)

        for s in remaining_list:
            student = s["student"]

            class_label = "-"

            if student["class_id"] is not None:
                class_row = class_service.get_class_by_id(
                    self.db,
                    student["class_id"]
                )

                if class_row:
                    class_label = class_row["name"]

                    if class_row["section"]:
                        class_label += (
                            f" - {class_row['section']}"
                        )

            self.tree.insert(
                "",
                "end",
                values=(
                    student["full_name"],
                    class_label,
                    f"{s['total_fee']:,.0f}",
                    f"{s['total_paid']:,.0f}",
                    f"{s['remaining']:,.0f}"
                ),
                tags=("owes",)
            )


# ==========================================================================
# Financial summary report
# ==========================================================================

class FinancialReportTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, padding=15)
        self.db = db

        self.label = ttk.Label(
            self,
            text="",
            font=("Segoe UI", 11),
            justify="left"
        )

        self.label.pack(
            anchor="w",
            pady=(0, 10)
        )

        ttk.Button(
            self,
            text="تازه‌سازی / Refresh",
            command=self.refresh
        ).pack(anchor="w")

        self.refresh()

    def refresh(self):
        fees_collected = payment_service.get_total_paid_all_students(
            self.db
        )

        other_income = finance_service.get_total_income(
            self.db
        )

        total_income = fees_collected + other_income

        direct_expenses = finance_service.get_total_expenses(
            self.db
        )

        salaries_paid = salary_service.get_total_salaries_paid(
            self.db
        )

        total_expenses = direct_expenses + salaries_paid

        net_income = total_income - total_expenses

        net_color = (
            "#166534"
            if net_income >= 0
            else "#b91c1c"
        )

        text = (
            f"عواید / INCOME\n"
            f"  مجموع فیس دریافت شده / Total Fees Collected:      "
            f"{fees_collected:,.0f}\n"
            f"  مجموع سایر عواید / Total Other Income:             "
            f"{other_income:,.0f}\n"
            f"  مجموع عواید کل / Total Income (Combined):          "
            f"{total_income:,.0f}\n\n"
            f"مصارف / EXPENSES\n"
            f"  مصارف مستقیم / Direct Expenses:                    "
            f"{direct_expenses:,.0f}\n"
            f"  مجموع معاشات / Total Salaries Paid:                "
            f"{salaries_paid:,.0f}\n"
            f"  مجموع مصارف کل / Total Expenses (Combined):        "
            f"{total_expenses:,.0f}\n\n"
            f"خالص عاید / NET INCOME:                              "
            f"{net_income:,.0f}"
        )

        self.label.config(
            text=text,
            foreground="black"
        )

        # Recolor just the net income line by rebuilding
        # with a second label
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Label) and widget is not self.label:
                widget.destroy()


# ==========================================================================
# Salaries report
# ==========================================================================

class SalariesReportTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, padding=15)
        self.db = db

        self.summary_label = ttk.Label(
            self,
            text="",
            font=("Segoe UI", 10, "bold")
        )

        self.summary_label.pack(
            anchor="w",
            pady=(0, 10)
        )

        columns = (
            "teacher",
            "month",
            "amount",
            "date"
        )

        # Container for list + scrollbar
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=14
        )

        headings = {
            "teacher": "استاد / Teacher",
            "month": "ماه / Month",
            "amount": "مبلغ / Amount",
            "date": "تاریخ / Date",
        }

        widths = {
            "teacher": 200,
            "month": 120,
            "amount": 130,
            "date": 130
        }

        for col in columns:
            self.tree.heading(
                col,
                text=headings[col]
            )

            self.tree.column(
                col,
                width=widths[col],
                anchor="center"
            )

        # Scrollbar for the list only
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        ttk.Button(
            self,
            text="تازه‌سازی / Refresh",
            command=self.refresh
        ).pack(
            anchor="w",
            pady=(10, 0)
        )

        self.refresh()

    def refresh(self):
        total = salary_service.get_total_salaries_paid(
            self.db
        )

        self.summary_label.config(
            text=(
                f"مجموع معاشات پرداخت شده / "
                f"Total Salaries Paid: {total:,.0f}"
            )
        )

        for row in self.tree.get_children():
            self.tree.delete(row)

        for s in salary_service.get_all_salaries(self.db):
            self.tree.insert(
                "",
                "end",
                values=(
                    s["teacher_name"],
                    s["month"] or "",
                    f"{s['amount']:,.0f}",
                    s["payment_date"]
                )
            )


# ==========================================================================
# Library report
# ==========================================================================

class LibraryReportTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, padding=15)
        self.db = db

        self.summary_label = ttk.Label(
            self,
            text="",
            font=("Segoe UI", 10, "bold")
        )

        self.summary_label.pack(
            anchor="w",
            pady=(0, 10)
        )

        columns = (
            "title",
            "author",
            "total",
            "available",
            "issued"
        )

        # Container for list + scrollbar
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=14
        )

        headings = {
            "title": "نام کتاب / Title",
            "author": "نویسنده / Author",
            "total": "کل / Total",
            "available": "موجود / Available",
            "issued": "توزیع شده / Issued",
        }

        widths = {
            "title": 220,
            "author": 150,
            "total": 90,
            "available": 100,
            "issued": 100
        }

        for col in columns:
            self.tree.heading(
                col,
                text=headings[col]
            )

            self.tree.column(
                col,
                width=widths[col],
                anchor="center"
            )

        # Scrollbar for the list only
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        ttk.Button(
            self,
            text="تازه‌سازی / Refresh",
            command=self.refresh
        ).pack(
            anchor="w",
            pady=(10, 0)
        )

        self.refresh()

    def refresh(self):
        total = library_service.get_total_books(
            self.db
        )

        available = library_service.get_total_available(
            self.db
        )

        issued = library_service.get_total_issued(
            self.db
        )

        self.summary_label.config(
            text=(
                f"مجموع کتاب‌ها / Total: {total}    "
                f"موجود / Available: {available}    "
                f"توزیع شده / Issued: {issued}"
            )
        )

        for row in self.tree.get_children():
            self.tree.delete(row)

        for b in library_service.get_all_books(self.db):
            issued_count = (
                b["total_copies"]
                - b["available_copies"]
            )

            self.tree.insert(
                "",
                "end",
                values=(
                    b["title"],
                    b["author"] or "",
                    b["total_copies"],
                    b["available_copies"],
                    issued_count
                )
            )