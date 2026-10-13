"""
ui/account.py

Change My Username/Password - available to ANY logged-in user (owner
or manager), but this screen only ever changes THEIR OWN account.
Requires the current password to confirm identity first.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from services import user_service


class AccountFrame(ttk.Frame):
    def __init__(self, parent, db, current_user, on_back, on_credentials_changed):
        super().__init__(parent, padding=20)
        self.db = db
        self.current_user = current_user
        self.on_back = on_back
        self.on_credentials_changed = on_credentials_changed

        self.pack(fill="both", expand=True)

        self._build_header()
        self._build_form()

    def _build_header(self):
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 20))

        ttk.Button(header, text="< بازگشت / Back", command=self.on_back).pack(side="left")

        ttk.Label(
            header, text="حساب من / My Account",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=15)

    def _build_form(self):
        form = ttk.LabelFrame(
            self,
            text="تغییر نام کاربری / رمز عبور - Change Username / Password",
            padding=15
        )
        form.pack(fill="x")

        ttk.Label(
            form,
            text=f"نام کاربری فعلی / Current Username: {self.current_user['username']}",
            font=("Segoe UI", 10, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=(0, 15))

        self.current_password_var = tk.StringVar()
        self.new_username_var = tk.StringVar()
        self.new_password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()

        ttk.Label(form, text="رمز عبور فعلی / Current Password:").grid(
            row=1, column=0, sticky="e", padx=5, pady=5
        )
        ttk.Entry(form, textvariable=self.current_password_var, show="*", width=28).grid(
            row=1, column=1, padx=5, pady=5
        )

        ttk.Separator(form, orient="horizontal").grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=10
        )

        ttk.Label(form, text="نام کاربری جدید / New Username:").grid(
            row=3, column=0, sticky="e", padx=5, pady=5
        )
        ttk.Entry(form, textvariable=self.new_username_var, width=28).grid(
            row=3, column=1, padx=5, pady=5
        )
        ttk.Label(
            form, text="(خالی = بدون تغییر / blank = no change)",
            font=("Segoe UI", 8), foreground="#888"
        ).grid(row=4, column=1, sticky="w", padx=5)

        ttk.Label(form, text="رمز عبور جدید / New Password:").grid(
            row=5, column=0, sticky="e", padx=5, pady=5
        )
        ttk.Entry(form, textvariable=self.new_password_var, show="*", width=28).grid(
            row=5, column=1, padx=5, pady=5
        )

        ttk.Label(form, text="تکرار رمز جدید / Confirm New Password:").grid(
            row=6, column=0, sticky="e", padx=5, pady=5
        )
        ttk.Entry(form, textvariable=self.confirm_password_var, show="*", width=28).grid(
            row=6, column=1, padx=5, pady=5
        )
        ttk.Label(
            form, text="(خالی = بدون تغییر / blank = no change)",
            font=("Segoe UI", 8), foreground="#888"
        ).grid(row=7, column=1, sticky="w", padx=5)

        ttk.Button(
            form, text="ذخیره تغییرات / Save Changes", command=self._handle_save
        ).grid(row=8, column=0, columnspan=2, pady=(15, 0))

    def _handle_save(self):
        new_password = self.new_password_var.get()
        confirm_password = self.confirm_password_var.get()

        if new_password != confirm_password:
            messagebox.showwarning("Invalid Input", "New password and confirmation do not match.")
            return

        try:
            new_username = user_service.change_own_credentials(
                self.db,
                self.current_user["id"],
                self.current_password_var.get(),
                self.new_username_var.get(),
                new_password,
            )
        except ValueError as e:
            messagebox.showwarning("Cannot Save", str(e))
            return
        except Exception as e:
            messagebox.showerror("Error", f"Could not save changes:\n{e}")
            return

        messagebox.showinfo(
            "Saved",
            f"Your account was updated successfully.\n\n"
            f"Username: {new_username}\n\n"
            f"You will be returned to the login screen - please log in again."
        )
        self.on_credentials_changed()