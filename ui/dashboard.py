"""
ui/dashboard.py

Main screen shown after login. Shows summary KPIs and a sidebar for
navigating to modules. "Manage Users" only appears for owner accounts.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from services.permissions import is_owner

NAV_ITEMS = [
    ("شاگردان / Students", "students"),
    ("استادان / Teachers", "teachers"),
    ("صنوف / Classes", "classes"),
    ("لیست صنوف / Class Rosters", "rosters"),
    ("ساختار فیس / Fee Structure", "fees"),
    ("پرداخت فیس / Payments", "payments"),
    ("مالی / Finance", "finance"),
    ("معاشات / Salaries", "salaries"),
    ("کتابخانه / Library", "library"),
    ("گزارش‌ها / Reports", "reports"),
    ("برامد اکسل / Excel Export", "excel_export"),
    ("بکاپ / Backup", "backup"),
    ("دوره‌های زمستانی / Winter Courses", "courses"),
    ("حساب من / My Account", "account"),
]

OWNER_ONLY_NAV_ITEMS = [
    ("مدیریت کاربران / Manage Users", "users"),
]


class DashboardFrame(ttk.Frame):
    def __init__(self, parent, db, current_user, on_logout, on_navigate):
        super().__init__(parent)
        self.db = db
        self.current_user = current_user
        self.on_logout = on_logout
        self.on_navigate = on_navigate

        self.pack(fill="both", expand=True)

        self._build_layout()
        self._build_sidebar()
        self._build_content_header()
        self._build_kpi_cards()

    def _build_layout(self):
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.sidebar = ttk.Frame(self, padding=10, width=230)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        self.content = ttk.Frame(self, padding=20)
        self.content.grid(row=0, column=1, sticky="nsew")

    def _build_sidebar(self):
        ttk.Label(
            self.sidebar, text="منو / Menu",
            font=("Segoe UI", 11, "bold")
        ).pack(pady=(0, 10), anchor="w")

        role_label = "مالک / Owner" if is_owner(self.current_user) else "مدیر / Manager"
        ttk.Label(
            self.sidebar, text=f"({role_label})",
            font=("Segoe UI", 9, "italic"), foreground="#666666"
        ).pack(pady=(0, 10), anchor="w")

        items = list(NAV_ITEMS)
        if is_owner(self.current_user):
            items += OWNER_ONLY_NAV_ITEMS

        for label, module_key in items:
            btn = ttk.Button(
                self.sidebar, text=label, width=27,
                command=lambda k=module_key, l=label: self._handle_nav_click(k, l)
            )
            btn.pack(pady=3, fill="x")

        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", pady=15)

        ttk.Button(
            self.sidebar, text="خروج / Logout", width=27,
            command=self.on_logout
        ).pack(pady=3, fill="x")

    def _handle_nav_click(self, module_key, label):
        self.on_navigate(module_key, label)

    def _build_content_header(self):
        header = ttk.Frame(self.content)
        header.pack(fill="x", pady=(0, 20))

        ttk.Label(
            header, text="داشبورد / Dashboard",
            font=("Segoe UI", 18, "bold")
        ).pack(side="left")

        today_str = date.today().strftime("%Y-%m-%d")
        ttk.Label(
            header, text=f"{today_str}   |   {self.current_user['username']}",
            font=("Segoe UI", 10), foreground="#666666"
        ).pack(side="right")

    def _build_kpi_cards(self):
        cards_frame = ttk.Frame(self.content)
        cards_frame.pack(fill="x")

        stats = self._load_stats()

        cards = [
            ("شاگردان فعال\nActive Students", stats["active_students"]),
            ("استادان فعال\nActive Teachers", stats["active_teachers"]),
            ("تعداد صنوف\nClasses", stats["classes"]),
            ("فیس دریافت شده (مجموع)\nTotal Fees Collected", stats["total_paid"]),
        ]

        for i, (label, value) in enumerate(cards):
            card = ttk.Frame(cards_frame, relief="groove", borderwidth=1, padding=15)
            card.grid(row=0, column=i, padx=8, sticky="nsew")
            cards_frame.columnconfigure(i, weight=1)

            ttk.Label(
                card, text=str(value), font=("Segoe UI", 20, "bold")
            ).pack()
            ttk.Label(
                card, text=label, font=("Segoe UI", 9),
                foreground="#555555", justify="center"
            ).pack(pady=(5, 0))

        note = ttk.Label(
            self.content,
            text="نوت: اطلاعات دوره‌های زمستانی جداگانه است و در این اعداد شامل نیست.\n"
                 "Note: Winter Course data is separate and not included in these numbers.",
            font=("Segoe UI", 8, "italic"), foreground="#888888",
            justify="left"
        )
        note.pack(anchor="w", pady=(20, 0))

    def _load_stats(self):
        active_students = self.db.fetchone(
            "SELECT COUNT(*) AS cnt FROM students WHERE status = 'active';"
        )["cnt"]

        active_teachers = self.db.fetchone(
            "SELECT COUNT(*) AS cnt FROM teachers WHERE status = 'active';"
        )["cnt"]

        classes_count = self.db.fetchone(
            "SELECT COUNT(*) AS cnt FROM classes;"
        )["cnt"]

        total_paid_row = self.db.fetchone(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM payments;"
        )
        total_paid = total_paid_row["total"]

        return {
            "active_students": active_students,
            "active_teachers": active_teachers,
            "classes": classes_count,
            "total_paid": f"{total_paid:,.0f}",
        }