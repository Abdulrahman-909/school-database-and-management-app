"""
ui/finance.py

Finance module: Income and Expenses, each with Add/Edit/Delete/Refresh,
plus a summary panel showing totals and net balance.

The Income and Expense lists each have their own vertical scrollbar.
All database access goes through services/finance_service.py.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from services import finance_service
from services import payment_service


# ============================================================================
# Categories
# ============================================================================

INCOME_CATEGORIES = [
    "ثبت نام",
    "کتاب",
    "ترانسپورت",
    "یونیفورم",
    "امتحان",
    "سایر",
]

EXPENSE_CATEGORIES = [
    "معاش استادان",
    "کرایه",
    "برق",
    "آب",
    "انترنت",
    "قرطاسیه",
    "کتاب",
    "ترمیمات",
    "وسایل",
    "نظافت",
    "امنیت",
    "ترانسپورت",
    "سایر",
]


# ============================================================================
# Finance Main Frame
# ============================================================================

class FinanceFrame(ttk.Frame):
    def __init__(self, parent, db, on_back):
        super().__init__(parent, padding=15)

        self.db = db
        self.on_back = on_back

        self.pack(fill="both", expand=True)

        self._build_header()
        self._build_summary()

        notebook = ttk.Notebook(self)
        notebook.pack(
            fill="both",
            expand=True,
            pady=(10, 0)
        )

        self.income_tab = IncomeTab(
            notebook,
            self.db,
            on_change=self.refresh_summary
        )

        self.expense_tab = ExpenseTab(
            notebook,
            self.db,
            on_change=self.refresh_summary
        )

        notebook.add(
            self.income_tab,
            text="عواید / Income"
        )

        notebook.add(
            self.expense_tab,
            text="مصارف / Expenses"
        )

        self.notebook = notebook

        self.refresh_summary()

    # ------------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------------

    def _build_header(self):
        header = ttk.Frame(self)
        header.pack(
            fill="x",
            pady=(0, 10)
        )

        ttk.Button(
            header,
            text="< بازگشت / Back",
            command=self.on_back
        ).pack(side="left")

        ttk.Label(
            header,
            text="مالی / Finance",
            font=("Segoe UI", 16, "bold")
        ).pack(
            side="left",
            padx=15
        )

    # ------------------------------------------------------------------------
    # Financial Summary
    # ------------------------------------------------------------------------

    def _build_summary(self):
        self.summary_frame = ttk.LabelFrame(
            self,
            text="خلص مالی / Financial Summary",
            padding=15
        )

        self.summary_frame.pack(
            fill="x"
        )

        self.summary_label = ttk.Label(
            self.summary_frame,
            text="",
            font=("Segoe UI", 10),
            justify="left"
        )

        self.summary_label.pack(
            anchor="w"
        )

    def refresh_summary(self):
        try:
            summary = finance_service.get_finance_summary(
                self.db
            )

            total_fees = payment_service.get_total_paid_all_students(
                self.db
            )

            balance_color = (
                "#166534"
                if summary["net_balance"] >= 0
                else "#b91c1c"
            )

            text = (
                f"مجموع عواید (غیر از فیس) / "
                f"Total Income (excl. tuition):   "
                f"{summary['total_income']:,.0f}\n"

                f"مجموع مصارف / Total Expenses:   "
                f"{summary['total_expenses']:,.0f}\n"

                f"باقی‌مانده خالص / Net Balance:   "
                f"{summary['net_balance']:,.0f}\n\n"

                f"مجموع فیس دریافت شده (جداگانه) / "
                f"Total Fees Collected (separate):   "
                f"{total_fees:,.0f}"
            )

            self.summary_label.config(
                text=text,
                foreground=balance_color
            )

        except Exception as e:
            self.summary_label.config(
                text=f"Could not load financial summary:\n{e}",
                foreground="#b91c1c"
            )


# ============================================================================
# Income Tab
# ============================================================================

class IncomeTab(ttk.Frame):
    def __init__(self, parent, db, on_change):
        super().__init__(
            parent,
            padding=10
        )

        self.db = db
        self.on_change = on_change
        self.selected_id = None

        self._build_form()
        self._build_list()

        self.refresh_list()

    # ------------------------------------------------------------------------
    # Income Form
    # ------------------------------------------------------------------------

    def _build_form(self):
        form = ttk.LabelFrame(
            self,
            text="افزودن / ویرایش عاید - Add / Edit Income",
            padding=15
        )

        form.pack(
            fill="x",
            pady=(0, 10)
        )

        self.source_var = tk.StringVar()
        self.amount_var = tk.StringVar()
        self.date_var = tk.StringVar(
            value=date.today().strftime("%Y-%m-%d")
        )
        self.note_var = tk.StringVar()

        # Source
        ttk.Label(
            form,
            text="نوع عاید / Source:"
        ).grid(
            row=0,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Combobox(
            form,
            textvariable=self.source_var,
            values=INCOME_CATEGORIES,
            width=22
        ).grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        # Amount
        ttk.Label(
            form,
            text="مبلغ / Amount:"
        ).grid(
            row=0,
            column=2,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.amount_var,
            width=22
        ).grid(
            row=0,
            column=3,
            padx=5,
            pady=5
        )

        # Date
        ttk.Label(
            form,
            text="تاریخ / Date:"
        ).grid(
            row=1,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.date_var,
            width=22
        ).grid(
            row=1,
            column=1,
            padx=5,
            pady=5
        )

        # Note
        ttk.Label(
            form,
            text="یادداشت / Note:"
        ).grid(
            row=1,
            column=2,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.note_var,
            width=22
        ).grid(
            row=1,
            column=3,
            padx=5,
            pady=5
        )

        # Buttons
        btn_frame = ttk.Frame(form)

        btn_frame.grid(
            row=2,
            column=0,
            columnspan=4,
            pady=(15, 0)
        )

        ttk.Button(
            btn_frame,
            text="ذخیره / Save",
            command=self._handle_save
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            btn_frame,
            text="پاک کردن / Clear",
            command=self._clear_form
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            btn_frame,
            text="حذف / Delete",
            command=self._handle_delete
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            btn_frame,
            text="تازه‌سازی / Refresh",
            command=self.refresh_list
        ).pack(
            side="left",
            padx=5
        )

    # ------------------------------------------------------------------------
    # Income List
    # ------------------------------------------------------------------------

    def _build_list(self):
        columns = (
            "id",
            "date",
            "source",
            "amount",
            "note"
        )

        # IMPORTANT:
        # The Treeview and scrollbar are inside their own frame.
        # This makes the scrollbar work correctly without scrolling
        # the entire Finance tab.
        list_frame = ttk.Frame(self)

        list_frame.pack(
            fill="both",
            expand=True
        )

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=10
        )

        headings = {
            "id": "ID",
            "date": "تاریخ / Date",
            "source": "نوع / Source",
            "amount": "مبلغ / Amount",
            "note": "یادداشت / Note"
        }

        widths = {
            "id": 50,
            "date": 110,
            "source": 140,
            "amount": 110,
            "note": 220
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

        # Vertical scrollbar
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        # Treeview
        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        # Scrollbar
        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self._handle_row_select
        )

    # ------------------------------------------------------------------------
    # Refresh Income List
    # ------------------------------------------------------------------------

    def refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            income_rows = finance_service.get_all_income(
                self.db
            )

            for i in income_rows:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        i["id"],
                        i["income_date"],
                        i["source"] or "",
                        f"{i['amount']:,.0f}",
                        i["note"] or ""
                    )
                )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not load income records:\n{e}"
            )

    # ------------------------------------------------------------------------
    # Select Income
    # ------------------------------------------------------------------------

    def _handle_row_select(self, event):
        selection = self.tree.selection()

        if not selection:
            return

        item = self.tree.item(
            selection[0]
        )

        income_id = item["values"][0]

        try:
            row = finance_service.get_income_by_id(
                self.db,
                income_id
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not load income record:\n{e}"
            )
            return

        if row is None:
            return

        self.selected_id = row["id"]

        self.source_var.set(
            row["source"] or ""
        )

        self.amount_var.set(
            str(row["amount"])
        )

        self.date_var.set(
            row["income_date"] or ""
        )

        self.note_var.set(
            row["note"] or ""
        )

    # ------------------------------------------------------------------------
    # Clear Income Form
    # ------------------------------------------------------------------------

    def _clear_form(self):
        self.selected_id = None

        self.source_var.set("")
        self.amount_var.set("")

        self.date_var.set(
            date.today().strftime("%Y-%m-%d")
        )

        self.note_var.set("")

        selection = self.tree.selection()

        if selection:
            self.tree.selection_remove(
                selection
            )

    # ------------------------------------------------------------------------
    # Save Income
    # ------------------------------------------------------------------------

    def _handle_save(self):
        try:
            if self.selected_id is None:

                finance_service.add_income(
                    self.db,
                    self.source_var.get(),
                    self.amount_var.get(),
                    self.date_var.get(),
                    self.note_var.get()
                )

                messagebox.showinfo(
                    "Saved",
                    "Income added successfully."
                )

            else:

                finance_service.update_income(
                    self.db,
                    self.selected_id,
                    self.source_var.get(),
                    self.amount_var.get(),
                    self.date_var.get(),
                    self.note_var.get()
                )

                messagebox.showinfo(
                    "Saved",
                    "Income updated successfully."
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
                f"Could not save income:\n{e}"
            )
            return

        self._clear_form()
        self.refresh_list()
        self.on_change()

    # ------------------------------------------------------------------------
    # Delete Income
    # ------------------------------------------------------------------------

    def _handle_delete(self):
        if self.selected_id is None:
            messagebox.showwarning(
                "No Selection",
                "Select an income entry first."
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Delete this income entry?"
        )

        if not confirm:
            return

        try:
            finance_service.delete_income(
                self.db,
                self.selected_id
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not delete:\n{e}"
            )
            return

        messagebox.showinfo(
            "Deleted",
            "Income entry deleted."
        )

        self._clear_form()
        self.refresh_list()
        self.on_change()


# ============================================================================
# Expense Tab
# ============================================================================

class ExpenseTab(ttk.Frame):
    def __init__(self, parent, db, on_change):
        super().__init__(
            parent,
            padding=10
        )

        self.db = db
        self.on_change = on_change
        self.selected_id = None

        self._build_form()
        self._build_list()

        self.refresh_list()

    # ------------------------------------------------------------------------
    # Expense Form
    # ------------------------------------------------------------------------

    def _build_form(self):
        form = ttk.LabelFrame(
            self,
            text="افزودن / ویرایش مصرف - Add / Edit Expense",
            padding=15
        )

        form.pack(
            fill="x",
            pady=(0, 10)
        )

        self.category_var = tk.StringVar()
        self.amount_var = tk.StringVar()

        self.date_var = tk.StringVar(
            value=date.today().strftime("%Y-%m-%d")
        )

        self.note_var = tk.StringVar()

        # Category
        ttk.Label(
            form,
            text="نوع مصرف / Category:"
        ).grid(
            row=0,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Combobox(
            form,
            textvariable=self.category_var,
            values=EXPENSE_CATEGORIES,
            width=22
        ).grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        # Amount
        ttk.Label(
            form,
            text="مبلغ / Amount:"
        ).grid(
            row=0,
            column=2,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.amount_var,
            width=22
        ).grid(
            row=0,
            column=3,
            padx=5,
            pady=5
        )

        # Date
        ttk.Label(
            form,
            text="تاریخ / Date:"
        ).grid(
            row=1,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.date_var,
            width=22
        ).grid(
            row=1,
            column=1,
            padx=5,
            pady=5
        )

        # Note
        ttk.Label(
            form,
            text="یادداشت / Note:"
        ).grid(
            row=1,
            column=2,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.note_var,
            width=22
        ).grid(
            row=1,
            column=3,
            padx=5,
            pady=5
        )

        # Buttons
        btn_frame = ttk.Frame(form)

        btn_frame.grid(
            row=2,
            column=0,
            columnspan=4,
            pady=(15, 0)
        )

        ttk.Button(
            btn_frame,
            text="ذخیره / Save",
            command=self._handle_save
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            btn_frame,
            text="پاک کردن / Clear",
            command=self._clear_form
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            btn_frame,
            text="حذف / Delete",
            command=self._handle_delete
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            btn_frame,
            text="تازه‌سازی / Refresh",
            command=self.refresh_list
        ).pack(
            side="left",
            padx=5
        )

    # ------------------------------------------------------------------------
    # Expense List
    # ------------------------------------------------------------------------

    def _build_list(self):
        columns = (
            "id",
            "date",
            "category",
            "amount",
            "note"
        )

        # Separate container for the list and scrollbar
        list_frame = ttk.Frame(self)

        list_frame.pack(
            fill="both",
            expand=True
        )

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=10
        )

        headings = {
            "id": "ID",
            "date": "تاریخ / Date",
            "category": "نوع / Category",
            "amount": "مبلغ / Amount",
            "note": "یادداشت / Note"
        }

        widths = {
            "id": 50,
            "date": 110,
            "category": 140,
            "amount": 110,
            "note": 220
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

        # Vertical scrollbar
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        # Treeview
        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        # Scrollbar
        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self._handle_row_select
        )

    # ------------------------------------------------------------------------
    # Refresh Expense List
    # ------------------------------------------------------------------------

    def refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            expense_rows = finance_service.get_all_expenses(
                self.db
            )

            for e in expense_rows:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        e["id"],
                        e["expense_date"],
                        e["category"] or "",
                        f"{e['amount']:,.0f}",
                        e["note"] or ""
                    )
                )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not load expense records:\n{e}"
            )

    # ------------------------------------------------------------------------
    # Select Expense
    # ------------------------------------------------------------------------

    def _handle_row_select(self, event):
        selection = self.tree.selection()

        if not selection:
            return

        item = self.tree.item(
            selection[0]
        )

        expense_id = item["values"][0]

        try:
            row = finance_service.get_expense_by_id(
                self.db,
                expense_id
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not load expense record:\n{e}"
            )
            return

        if row is None:
            return

        self.selected_id = row["id"]

        self.category_var.set(
            row["category"] or ""
        )

        self.amount_var.set(
            str(row["amount"])
        )

        self.date_var.set(
            row["expense_date"] or ""
        )

        self.note_var.set(
            row["note"] or ""
        )

    # ------------------------------------------------------------------------
    # Clear Expense Form
    # ------------------------------------------------------------------------

    def _clear_form(self):
        self.selected_id = None

        self.category_var.set("")
        self.amount_var.set("")

        self.date_var.set(
            date.today().strftime("%Y-%m-%d")
        )

        self.note_var.set("")

        selection = self.tree.selection()

        if selection:
            self.tree.selection_remove(
                selection
            )

    # ------------------------------------------------------------------------
    # Save Expense
    # ------------------------------------------------------------------------

    def _handle_save(self):
        try:
            if self.selected_id is None:

                finance_service.add_expense(
                    self.db,
                    self.category_var.get(),
                    self.amount_var.get(),
                    self.date_var.get(),
                    self.note_var.get()
                )

                messagebox.showinfo(
                    "Saved",
                    "Expense added successfully."
                )

            else:

                finance_service.update_expense(
                    self.db,
                    self.selected_id,
                    self.category_var.get(),
                    self.amount_var.get(),
                    self.date_var.get(),
                    self.note_var.get()
                )

                messagebox.showinfo(
                    "Saved",
                    "Expense updated successfully."
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
                f"Could not save expense:\n{e}"
            )
            return

        self._clear_form()
        self.refresh_list()
        self.on_change()

    # ------------------------------------------------------------------------
    # Delete Expense
    # ------------------------------------------------------------------------

    def _handle_delete(self):
        if self.selected_id is None:
            messagebox.showwarning(
                "No Selection",
                "Select an expense entry first."
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Delete this expense entry?"
        )

        if not confirm:
            return

        try:
            finance_service.delete_expense(
                self.db,
                self.selected_id
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not delete:\n{e}"
            )
            return

        messagebox.showinfo(
            "Deleted",
            "Expense entry deleted."
        )

        self._clear_form()
        self.refresh_list()
        self.on_change()