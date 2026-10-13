"""
ui/salaries.py

Teacher Salaries module: Add / Edit / Delete / Refresh.
Selecting a teacher auto-fills their base salary amount (editable).
All database access goes through services/salary_service.py and
services/teacher_service.py (for the teacher dropdown).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from services import salary_service
from services import teacher_service


class SalariesFrame(ttk.Frame):
    def __init__(self, parent, db, on_back):
        super().__init__(parent, padding=15)
        self.db = db
        self.on_back = on_back

        self.selected_salary_id = None
        self.teacher_options = []  # list of (id, label)

        self.pack(fill="both", expand=True)

        self._build_header()
        self._build_summary()
        self._build_form()
        self._build_list()

        self.refresh_list()

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _build_header(self):
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 10))

        ttk.Button(header, text="< بازگشت / Back", command=self.on_back).pack(side="left")

        ttk.Label(
            header, text="معاشات استادان / Teacher Salaries",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=15)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _build_summary(self):
        self.summary_label = ttk.Label(self, text="", font=("Segoe UI", 10, "bold"))
        self.summary_label.pack(anchor="w", pady=(0, 10))

    def _refresh_summary(self):
        total = salary_service.get_total_salaries_paid(self.db)
        self.summary_label.config(
            text=f"مجموع معاشات پرداخت شده / Total Salaries Paid: {total:,.0f}"
        )

    # ------------------------------------------------------------------
    # Form
    # ------------------------------------------------------------------

    def _build_form(self):
        form = ttk.LabelFrame(self, text="افزودن / ویرایش معاش - Add / Edit Salary", padding=15)
        form.pack(fill="x", pady=(0, 10))

        self.teacher_var = tk.StringVar()
        self.amount_var = tk.StringVar()
        self.date_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        self.month_var = tk.StringVar()
        self.note_var = tk.StringVar()

        ttk.Label(form, text="استاد / Teacher:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.teacher_combo = ttk.Combobox(
            form, textvariable=self.teacher_var, values=[], state="readonly", width=25
        )
        self.teacher_combo.grid(row=0, column=1, padx=5, pady=5)
        self.teacher_combo.bind("<<ComboboxSelected>>", self._handle_teacher_selected)

        ttk.Label(form, text="مبلغ / Amount:").grid(row=0, column=2, sticky="e", padx=5, pady=5)
        ttk.Entry(form, textvariable=self.amount_var, width=25).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form, text="ماه / Month:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(form, textvariable=self.month_var, width=25).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form, text="تاریخ پرداخت / Payment Date:").grid(row=1, column=2, sticky="e", padx=5, pady=5)
        ttk.Entry(form, textvariable=self.date_var, width=25).grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(form, text="یادداشت / Note:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(form, textvariable=self.note_var, width=25).grid(row=2, column=1, padx=5, pady=5)

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=(15, 0))

        ttk.Button(btn_frame, text="ذخیره / Save", command=self._handle_save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="پاک کردن فورم / Clear Form", command=self._clear_form).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="حذف / Delete", command=self._handle_delete).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="تازه‌سازی / Refresh", command=self._handle_refresh).pack(side="left", padx=5)

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def _build_list(self):
        columns = ("id", "teacher", "month", "amount", "date", "note")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=12)

        headings = {
            "id": "ID",
            "teacher": "استاد / Teacher",
            "month": "ماه / Month",
            "amount": "مبلغ / Amount",
            "date": "تاریخ / Date",
            "note": "یادداشت / Note",
        }
        widths = {"id": 50, "teacher": 170, "month": 100, "amount": 110, "date": 110, "note": 180}

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")

        # --------------------------------------------------------------
        # Scrollbar for the salary LIST ONLY
        # --------------------------------------------------------------

        scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(
            side="right",
            fill="y",
            pady=(5, 0)
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True,
            pady=(5, 0)
        )

        self.tree.bind("<<TreeviewSelect>>", self._handle_row_select)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def refresh_list(self):
        self._load_teacher_options()
        self._refresh_summary()

        for row in self.tree.get_children():
            self.tree.delete(row)

        salaries = salary_service.get_all_salaries(self.db)
        for s in salaries:
            self.tree.insert("", "end", values=(
                s["id"], s["teacher_name"], s["month"] or "",
                f"{s['amount']:,.0f}", s["payment_date"], s["note"] or ""
            ))

    def _handle_refresh(self):
        self._clear_form()
        self.refresh_list()

    def _load_teacher_options(self):
        self.teacher_options = teacher_service.get_teacher_options(self.db)
        labels = [label for (_id, label) in self.teacher_options]
        self.teacher_combo["values"] = labels
        if not labels:
            self.teacher_combo.set("")

    def _teacher_id_from_label(self, label):
        for teacher_id, opt_label in self.teacher_options:
            if opt_label == label:
                return teacher_id
        return None

    def _teacher_label_from_id(self, teacher_id):
        for opt_id, label in self.teacher_options:
            if opt_id == teacher_id:
                return label
        return ""

    # ------------------------------------------------------------------
    # Teacher selection -> auto-fill amount
    # ------------------------------------------------------------------

    def _handle_teacher_selected(self, event):
        # Only auto-fill when adding a NEW salary entry, not while
        # editing an existing one (so we don't overwrite a historical
        # amount just because the dropdown was touched).
        if self.selected_salary_id is not None:
            return

        teacher_id = self._teacher_id_from_label(self.teacher_var.get())
        if teacher_id is None:
            return

        base_salary = salary_service.get_teacher_base_salary(self.db, teacher_id)
        if base_salary is not None:
            self.amount_var.set(str(base_salary))

    # ------------------------------------------------------------------
    # Form <-> selection
    # ------------------------------------------------------------------

    def _handle_row_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        salary_id = item["values"][0]

        salary = salary_service.get_salary_by_id(self.db, salary_id)
        if salary is None:
            return

        self.selected_salary_id = salary["id"]
        self.teacher_var.set(self._teacher_label_from_id(salary["teacher_id"]))
        self.amount_var.set(str(salary["amount"]))
        self.date_var.set(salary["payment_date"] or "")
        self.month_var.set(salary["month"] or "")
        self.note_var.set(salary["note"] or "")

    def _clear_form(self):
        self.selected_salary_id = None
        self.teacher_var.set("")
        self.amount_var.set("")
        self.date_var.set(date.today().strftime("%Y-%m-%d"))
        self.month_var.set("")
        self.note_var.set("")
        self.tree.selection_remove(self.tree.selection())

    # ------------------------------------------------------------------
    # Save / Delete
    # ------------------------------------------------------------------

    def _handle_save(self):
        teacher_id = self._teacher_id_from_label(self.teacher_var.get())

        try:
            if self.selected_salary_id is None:
                salary_service.add_salary(
                    self.db, teacher_id, self.amount_var.get(),
                    self.date_var.get(), self.month_var.get(), self.note_var.get()
                )
                messagebox.showinfo("Saved", "Salary payment recorded successfully.")
            else:
                salary_service.update_salary(
                    self.db, self.selected_salary_id, teacher_id, self.amount_var.get(),
                    self.date_var.get(), self.month_var.get(), self.note_var.get()
                )
                messagebox.showinfo("Saved", "Salary payment updated successfully.")
        except ValueError as e:
            messagebox.showwarning("Invalid Input", str(e))
            return
        except Exception as e:
            messagebox.showerror("Error", f"Could not save salary payment:\n{e}")
            return

        self._clear_form()
        self.refresh_list()

    def _handle_delete(self):
        if self.selected_salary_id is None:
            messagebox.showwarning("No Selection", "Select a salary entry from the list first.")
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this salary payment?\nThis cannot be undone."
        )
        if not confirm:
            return

        try:
            salary_service.delete_salary(self.db, self.selected_salary_id)
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete salary payment:\n{e}")
            return

        messagebox.showinfo("Deleted", "Salary payment deleted.")
        self._clear_form()
        self.refresh_list()