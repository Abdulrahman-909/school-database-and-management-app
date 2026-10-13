"""
ui/login.py

Login screen. Shows a one-time "create owner account" form if the
users table is empty, otherwise shows the normal login form.
"""

import tkinter as tk
from tkinter import ttk, messagebox


class LoginFrame(ttk.Frame):
    def __init__(self, parent, db, on_login_success):
        super().__init__(parent, padding=40)
        self.db = db
        self.on_login_success = on_login_success

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.confirm_var = tk.StringVar()

        self.error_label = None

        if self._users_table_is_empty():
            self._build_create_owner_form()
        else:
            self._build_login_form()

    def _users_table_is_empty(self) -> bool:
        row = self.db.fetchone("SELECT COUNT(*) AS cnt FROM users;")
        return row["cnt"] == 0

    def _clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def _build_create_owner_form(self):
        self._clear()

        ttk.Label(
            self, text="خوش آمدید - این اولین بار است",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(0, 5))

        ttk.Label(
            self, text="No owner account exists yet. Create one to continue.",
            font=("Segoe UI", 9, "italic"), foreground="#666666"
        ).grid(row=1, column=0, columnspan=2, pady=(0, 20))

        ttk.Label(self, text="Username:").grid(row=2, column=0, sticky="e", padx=5, pady=8)
        ttk.Entry(self, textvariable=self.username_var, width=28).grid(row=2, column=1, pady=8)

        ttk.Label(self, text="Password:").grid(row=3, column=0, sticky="e", padx=5, pady=8)
        ttk.Entry(self, textvariable=self.password_var, show="*", width=28).grid(row=3, column=1, pady=8)

        ttk.Label(self, text="Confirm Password:").grid(row=4, column=0, sticky="e", padx=5, pady=8)
        ttk.Entry(self, textvariable=self.confirm_var, show="*", width=28).grid(row=4, column=1, pady=8)

        self.error_label = ttk.Label(self, text="", foreground="red")
        self.error_label.grid(row=5, column=0, columnspan=2, pady=(5, 5))

        ttk.Button(
            self, text="Create Owner Account", command=self._handle_create_owner
        ).grid(row=6, column=0, columnspan=2, pady=(10, 0))

    def _handle_create_owner(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        confirm = self.confirm_var.get()

        if not username or not password:
            self._show_error("Username and password are required.")
            return
        if password != confirm:
            self._show_error("Passwords do not match.")
            return
        if len(password) < 4:
            self._show_error("Password must be at least 4 characters.")
            return

        try:
            self.db.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?);",
                (username, password, "owner")
            )
        except Exception as e:
            self._show_error(f"Could not create account: {e}")
            return

        messagebox.showinfo(
            "Account Created",
            f"Owner account '{username}' created successfully.\nPlease log in."
        )

        self.username_var.set(username)
        self.password_var.set("")
        self._build_login_form()

    def _build_login_form(self):
        self._clear()

        ttk.Label(
            self, text="سیستم مدیریت مکتب - Login",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(0, 25))

        ttk.Label(self, text="Username:").grid(row=1, column=0, sticky="e", padx=5, pady=8)
        username_entry = ttk.Entry(self, textvariable=self.username_var, width=28)
        username_entry.grid(row=1, column=1, pady=8)

        ttk.Label(self, text="Password:").grid(row=2, column=0, sticky="e", padx=5, pady=8)
        password_entry = ttk.Entry(self, textvariable=self.password_var, show="*", width=28)
        password_entry.grid(row=2, column=1, pady=8)

        self.error_label = ttk.Label(self, text="", foreground="red")
        self.error_label.grid(row=3, column=0, columnspan=2, pady=(5, 5))

        ttk.Button(
            self, text="Login", command=self._handle_login
        ).grid(row=4, column=0, columnspan=2, pady=(15, 0))

        password_entry.bind("<Return>", lambda event: self._handle_login())
        username_entry.bind("<Return>", lambda event: self._handle_login())

        if self.username_var.get():
            password_entry.focus_set()
        else:
            username_entry.focus_set()

    def _handle_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username or not password:
            self._show_error("Enter both username and password.")
            return

        user = self.db.fetchone(
            "SELECT * FROM users WHERE username = ?;", (username,)
        )

        if user is None or user["password"] != password:
            self._show_error("نام کاربری یا رمز عبور اشتباه است / Invalid username or password.")
            return

        self._show_error("")
        self.on_login_success(user)

    def _show_error(self, message: str):
        if self.error_label is not None:
            self.error_label.config(text=message)