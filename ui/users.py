"""
ui/users.py

Manage Users module (owner only).

Features:
- Create manager accounts
- View all user accounts
- Delete manager accounts
- Vertical scrollbar for the users list
- Access restricted to the school owner
"""

import tkinter as tk
from tkinter import ttk, messagebox

from services import user_service
from services.permissions import is_owner


class UsersFrame(ttk.Frame):
    def __init__(self, parent, db, current_user, on_back):
        super().__init__(parent, padding=15)

        self.db = db
        self.current_user = current_user
        self.on_back = on_back
        self.selected_id = None

        self.pack(fill="both", expand=True)

        # Only the school owner can access this page
        if not is_owner(current_user):
            self._build_denied()
            return

        self._build_header()
        self._build_form()
        self._build_list()

        self.refresh_list()

    # ==============================================================
    # ACCESS DENIED
    # ==============================================================

    def _build_denied(self):
        ttk.Button(
            self,
            text="< بازگشت / Back",
            command=self.on_back
        ).pack(anchor="w")

        ttk.Label(
            self,
            text=(
                "دسترسی محدود / Access Restricted\n\n"
                "این صفحه فقط برای مالک مکتب است.\n"
                "This page is for the school owner only."
            ),
            font=("Segoe UI", 12),
            foreground="#b91c1c",
            justify="center"
        ).pack(fill="both", expand=True)

    # ==============================================================
    # HEADER
    # ==============================================================

    def _build_header(self):
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 15))

        ttk.Button(
            header,
            text="< بازگشت / Back",
            command=self.on_back
        ).pack(side="left")

        ttk.Label(
            header,
            text="مدیریت کاربران / Manage Users",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=15)

    # ==============================================================
    # ADD USER FORM
    # ==============================================================

    def _build_form(self):
        form = ttk.LabelFrame(
            self,
            text="افزودن کارمند مدیر / Add Manager Account",
            padding=15
        )
        form.pack(fill="x", pady=(0, 15))

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        # Username
        ttk.Label(
            form,
            text="نام کاربری / Username:"
        ).grid(
            row=0,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.username_var,
            width=25
        ).grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        # Password
        ttk.Label(
            form,
            text="رمز عبور / Password:"
        ).grid(
            row=0,
            column=2,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.password_var,
            show="*",
            width=25
        ).grid(
            row=0,
            column=3,
            padx=5,
            pady=5
        )

        # Create button
        ttk.Button(
            form,
            text="ایجاد حساب مدیر / Create Manager Account",
            command=self._handle_add
        ).grid(
            row=1,
            column=0,
            columnspan=4,
            pady=(10, 0)
        )

        # Information
        ttk.Label(
            form,
            text=(
                "نوت: حساب‌های «مدیر» نمی‌توانند رکوردهای مالی را حذف کنند، "
                "بکاپ را بازگردانند/حذف کنند،\n"
                "یا تعداد کل کتاب‌ها را افزایش دهند.\n\n"
                "Note: 'manager' accounts cannot delete financial records, "
                "restore/delete backups,\n"
                "or increase total book copies."
            ),
            font=("Segoe UI", 8, "italic"),
            foreground="#888888",
            justify="left"
        ).grid(
            row=2,
            column=0,
            columnspan=4,
            sticky="w",
            pady=(10, 0)
        )

    # ==============================================================
    # USERS LIST
    # ==============================================================

    def _build_list(self):
        list_frame = ttk.LabelFrame(
            self,
            text="لیست کاربران / User Accounts",
            padding=8
        )
        list_frame.pack(
            fill="both",
            expand=True,
            pady=(0, 10)
        )

        # Container for Treeview + scrollbar
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(
            fill="both",
            expand=True
        )

        columns = (
            "id",
            "username",
            "role",
            "created"
        )

        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=10
        )

        headings = {
            "id": "ID",
            "username": "نام کاربری / Username",
            "role": "نقش / Role",
            "created": "تاریخ ایجاد / Created"
        }

        widths = {
            "id": 60,
            "username": 220,
            "role": 150,
            "created": 180
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

        # ==========================================================
        # VERTICAL SCROLLBAR
        # ==========================================================

        scrollbar = ttk.Scrollbar(
            tree_frame,
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

        # Select user
        self.tree.bind(
            "<<TreeviewSelect>>",
            self._handle_row_select
        )

        # ==========================================================
        # DELETE BUTTON
        # ==========================================================

        ttk.Button(
            list_frame,
            text="حذف کاربر انتخاب شده / Delete Selected User",
            command=self._handle_delete
        ).pack(
            anchor="w",
            pady=(10, 2)
        )

        # ==========================================================
        # OPTIONAL MOUSE WHEEL SUPPORT
        # ==========================================================

        def _on_mousewheel(event):
            self.tree.yview_scroll(
                int(-1 * (event.delta / 120)),
                "units"
            )

        self.tree.bind(
            "<Enter>",
            lambda event: self.tree.bind(
                "<MouseWheel>",
                _on_mousewheel
            )
        )

        self.tree.bind(
            "<Leave>",
            lambda event: self.tree.unbind(
                "<MouseWheel>"
            )
        )

    # ==============================================================
    # REFRESH USERS
    # ==============================================================

    def refresh_list(self):
        # Remove existing rows
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Get users from database
        users = user_service.get_all_users(self.db)

        for user in users:
            role_display = (
                "مالک / Owner"
                if user["role"] in ("owner", "admin")
                else "مدیر / Manager"
            )

            self.tree.insert(
                "",
                "end",
                values=(
                    user["id"],
                    user["username"],
                    role_display,
                    user["created_at"] or ""
                )
            )

    # ==============================================================
    # SELECT USER
    # ==============================================================

    def _handle_row_select(self, event):
        selection = self.tree.selection()

        if not selection:
            self.selected_id = None
            return

        item = self.tree.item(selection[0])

        values = item.get("values", [])

        if not values:
            self.selected_id = None
            return

        self.selected_id = values[0]

    # ==============================================================
    # ADD MANAGER
    # ==============================================================

    def _handle_add(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()

        try:
            user_service.add_manager_user(
                self.db,
                username,
                password
            )

        except ValueError as e:
            messagebox.showwarning(
                "Invalid Input",
                str(e)
            )
            return

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not create account:\n{e}"
            )
            return

        messagebox.showinfo(
            "Created",
            "Manager account created."
        )

        self.username_var.set("")
        self.password_var.set("")

        self.refresh_list()

    # ==============================================================
    # DELETE USER
    # ==============================================================

    def _handle_delete(self):
        if self.selected_id is None:
            messagebox.showwarning(
                "No Selection",
                "Select a user first."
            )
            return

        # Extra protection against accidental deletion
        if not messagebox.askyesno(
            "Confirm Delete",
            "Delete this user account?\n\n"
            "This action cannot be undone."
        ):
            return

        try:
            user_service.delete_user(
                self.db,
                self.selected_id,
                self.current_user["id"]
            )

        except ValueError as e:
            messagebox.showwarning(
                "Cannot Delete",
                str(e)
            )
            return

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not delete:\n{e}"
            )
            return

        messagebox.showinfo(
            "Deleted",
            "User deleted."
        )

        self.selected_id = None

        self.refresh_list()