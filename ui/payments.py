"""
ui/payments.py

Student Payments module. Fees are tracked MONTHLY: Fee Structure's
amount is per-month, and every payment must be tagged with one of the
12 months, so each month can be paid/tracked independently. Deleting a
payment record is restricted to the owner (see services/permissions.py).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from services import payment_service
from services.payment_service import MONTH_NAMES
from services import student_service
from services import receipt_service
from services.permissions import check_owner_action


class PaymentsFrame(ttk.Frame):
    _last_student_label = None
    _last_year = None

    def __init__(self, parent, db, current_user, on_back):
        super().__init__(parent, padding=15)
        self.db = db
        self.current_user = current_user
        self.on_back = on_back

        self.student_options = []
        self.current_student_id = None
        self.current_student_name = None
        self.current_year = None
        self.selected_payment_id = None

        self.pack(fill="both", expand=True)

        # --------------------------------------------------------------
        # OUTER SCROLLBAR FOR THE ENTIRE PAYMENTS TAB
        # --------------------------------------------------------------

        self.canvas = tk.Canvas(
            self,
            highlightthickness=0,
            borderwidth=0
        )

        self.outer_scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )

        self.canvas.configure(
            yscrollcommand=self.outer_scrollbar.set
        )

        self.outer_scrollbar.pack(
            side="right",
            fill="y"
        )

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.content_frame = ttk.Frame(self.canvas)

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.content_frame,
            anchor="nw"
        )

        self.content_frame.bind(
            "<Configure>",
            self._update_scrollregion
        )

        self.canvas.bind(
            "<Configure>",
            self._resize_content
        )

        self._build_header()
        self._build_selector()
        self._build_summary()
        self._build_monthly_breakdown()
        self._build_payment_form()
        self._build_history_list()

        self._load_student_options()

        if PaymentsFrame._last_student_label:
            self.student_var.set(PaymentsFrame._last_student_label)
        if PaymentsFrame._last_year:
            self.year_var.set(PaymentsFrame._last_year)
        if PaymentsFrame._last_student_label and PaymentsFrame._last_year:
            self._handle_load()

    # ------------------------------------------------------------------
    # Outer scrollbar helpers
    # ------------------------------------------------------------------

    def _update_scrollregion(self, event=None):
        self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        )

    def _resize_content(self, event):
        self.canvas.itemconfigure(
            self.canvas_window,
            width=event.width
        )

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _build_header(self):
        header = ttk.Frame(self.content_frame)
        header.pack(fill="x", pady=(0, 10))

        ttk.Button(
            header,
            text="< بازگشت / Back",
            command=self.on_back
        ).pack(side="left")

        ttk.Label(
            header,
            text="پرداخت فیس / Student Payments",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=15)

    # ------------------------------------------------------------------
    # Student + academic year selector
    # ------------------------------------------------------------------

    def _build_selector(self):
        sel_frame = ttk.LabelFrame(
            self.content_frame,
            text="انتخاب شاگرد / Select Student",
            padding=15
        )
        sel_frame.pack(fill="x", pady=(0, 10))

        self.student_var = tk.StringVar()
        self.year_var = tk.StringVar(value=str(date.today().year))

        ttk.Label(
            sel_frame,
            text="شاگرد / Student:"
        ).grid(row=0, column=0, sticky="e", padx=5, pady=5)

        self.student_combo = ttk.Combobox(
            sel_frame,
            textvariable=self.student_var,
            values=[],
            state="readonly",
            width=35
        )
        self.student_combo.grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Label(
            sel_frame,
            text="سال تعلیمی / Academic Year:"
        ).grid(row=0, column=2, sticky="e", padx=5, pady=5)

        ttk.Entry(
            sel_frame,
            textvariable=self.year_var,
            width=15
        ).grid(
            row=0,
            column=3,
            padx=5,
            pady=5
        )

        ttk.Button(
            sel_frame,
            text="بارگذاری / Load",
            command=self._handle_load
        ).grid(
            row=0,
            column=4,
            padx=10,
            pady=5
        )

    # ------------------------------------------------------------------
    # Annual fee summary
    # ------------------------------------------------------------------

    def _build_summary(self):
        self.summary_frame = ttk.LabelFrame(
            self.content_frame,
            text="خلص سالانه فیس / Annual Fee Summary",
            padding=15
        )
        self.summary_frame.pack(
            fill="x",
            pady=(0, 10)
        )

        self.summary_label = ttk.Label(
            self.summary_frame,
            text="شاگرد را انتخاب و «بارگذاری» را کلیک کنید.\n"
                 "Select a student and click Load.",
            font=("Segoe UI", 10),
            foreground="#666666",
            justify="left"
        )
        self.summary_label.pack(anchor="w")

    def _render_summary(self, summary):
        student = summary["student"]

        if not summary["fee_defined"]:
            text = (
                f"شاگرد / Student: {student['full_name']}\n\n"
                f"⚠ برای این صنف و سال تعلیمی هنوز فیس تعیین نشده است.\n"
                f"No fee structure has been set for this student's class and year yet.\n"
                f"برو به «ساختار فیس» و فیس ماهانه را تعریف کنید.\n"
                f"Go to Fee Structure and define a monthly fee first."
            )
            self.summary_label.config(
                text=text,
                foreground="#b45309"
            )
            return

        text = (
            f"شاگرد / Student: {student['full_name']}\n"
            f"فیس ماهانه / Monthly Fee:        {summary['monthly_fee']:,.0f}\n"
            f"مجموع سالانه (۹ ماه) / Annual Total (x9):  {summary['total_fee']:,.0f}\n"
            f"مجموع پرداخت شده / Total Paid:      {summary['total_paid']:,.0f}\n"
            f"باقی مانده سالانه / Annual Remaining:   {summary['remaining']:,.0f}"
        )

        color = "#166534" if summary["remaining"] <= 0 else "#000000"

        self.summary_label.config(
            text=text,
            foreground=color
        )

    # ------------------------------------------------------------------
    # 12-month breakdown
    # ------------------------------------------------------------------

    def _build_monthly_breakdown(self):
        frame = ttk.LabelFrame(
            self.content_frame,
            text="تفکیک ماهانه / Monthly Breakdown",
            padding=10
        )
        frame.pack(
            fill="x",
            pady=(0, 10)
        )

        columns = ("month", "due", "paid", "remaining")

        self.month_tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=12
        )

        headings = {
            "month": "ماه / Month",
            "due": "قابل پرداخت / Due",
            "paid": "پرداخت شده / Paid",
            "remaining": "باقی مانده / Remaining"
        }

        widths = {
            "month": 100,
            "due": 110,
            "paid": 110,
            "remaining": 110
        }

        for col in columns:
            self.month_tree.heading(
                col,
                text=headings[col]
            )
            self.month_tree.column(
                col,
                width=widths[col],
                anchor="center"
            )

        self.month_tree.tag_configure(
            "paid_full",
            background="#c6efce"
        )

        self.month_tree.tag_configure(
            "owing",
            background="#f8d7da"
        )

        self.month_tree.pack(
            fill="x"
        )

    def _refresh_monthly_breakdown(self, fee_defined):
        for row in self.month_tree.get_children():
            self.month_tree.delete(row)

        if not fee_defined or self.current_student_id is None:
            return

        breakdown = payment_service.get_month_breakdown(
            self.db,
            self.current_student_id,
            self.current_year
        )

        for m in breakdown:
            tag = "paid_full" if m["remaining"] <= 0 else "owing"

            self.month_tree.insert(
                "",
                "end",
                values=(
                    m["month"],
                    f"{m['due']:,.0f}",
                    f"{m['paid']:,.0f}",
                    f"{m['remaining']:,.0f}"
                ),
                tags=(tag,)
            )

    # ------------------------------------------------------------------
    # Add payment form
    # ------------------------------------------------------------------

    def _build_payment_form(self):
        form = ttk.LabelFrame(
            self.content_frame,
            text="ثبت پرداخت جدید / Record New Payment",
            padding=15
        )
        form.pack(
            fill="x",
            pady=(0, 10)
        )

        self.amount_var = tk.StringVar()
        self.month_var = tk.StringVar()
        self.date_var = tk.StringVar(
            value=date.today().strftime("%Y-%m-%d")
        )
        self.note_var = tk.StringVar()
        self.received_by_var = tk.StringVar()
        self.allow_overpay_var = tk.BooleanVar(value=False)

        ttk.Label(
            form,
            text="ماه / Month:"
        ).grid(
            row=0,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Combobox(
            form,
            textvariable=self.month_var,
            values=MONTH_NAMES,
            state="readonly",
            width=18
        ).grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

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
            width=18
        ).grid(
            row=0,
            column=3,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="تاریخ / Date (YYYY-MM-DD):"
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
            width=18
        ).grid(
            row=1,
            column=1,
            padx=5,
            pady=5
        )

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
            width=18
        ).grid(
            row=1,
            column=3,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="دریافت کننده / Received By:"
        ).grid(
            row=2,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.received_by_var,
            width=18
        ).grid(
            row=2,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Checkbutton(
            form,
            text="اجازه پرداخت اضافی / Allow overpayment",
            variable=self.allow_overpay_var
        ).grid(
            row=2,
            column=2,
            columnspan=2,
            sticky="w",
            padx=5,
            pady=(10, 0)
        )

        btn_frame = ttk.Frame(form)
        btn_frame.grid(
            row=3,
            column=0,
            columnspan=4,
            pady=(10, 0)
        )

        ttk.Button(
            btn_frame,
            text="ثبت پرداخت / Save Payment",
            command=self._handle_save_payment
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            btn_frame,
            text="حذف پرداخت انتخاب شده / Delete Selected",
            command=self._handle_delete_payment
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            btn_frame,
            text="چاپ رسید / Print Receipt",
            command=self._handle_print_receipt
        ).pack(
            side="left",
            padx=5
        )

    # ------------------------------------------------------------------
    # Payment history list
    # ------------------------------------------------------------------

    def _build_history_list(self):
        ttk.Label(
            self.content_frame,
            text="تاریخچه پرداخت / Payment History",
            font=("Segoe UI", 11, "bold")
        ).pack(
            anchor="w",
            pady=(5, 5)
        )

        # --------------------------------------------------------------
        # INNER SCROLLBAR ONLY FOR PAYMENT HISTORY
        # --------------------------------------------------------------

        history_frame = ttk.Frame(self.content_frame)

        history_frame.pack(
            fill="both",
            expand=True
        )

        columns = (
            "student",
            "month",
            "date",
            "amount",
            "note",
            "received_by",
            "id"
        )

        self.tree = ttk.Treeview(
            history_frame,
            columns=columns,
            show="headings",
            height=10
        )

        headings = {
            "student": "شاگرد / Student",
            "month": "ماه / Month",
            "date": "تاریخ / Date",
            "amount": "مبلغ / Amount",
            "note": "یادداشت / Note",
            "received_by": "دریافت کننده / Received By",
            "id": "ID",
        }

        widths = {
            "student": 160,
            "month": 90,
            "date": 100,
            "amount": 100,
            "note": 160,
            "received_by": 130,
            "id": 50
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

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        history_scrollbar = ttk.Scrollbar(
            history_frame,
            orient="vertical",
            command=self.tree.yview
        )

        history_scrollbar.pack(
            side="right",
            fill="y"
        )

        self.tree.configure(
            yscrollcommand=history_scrollbar.set
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self._handle_row_select
        )

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_student_options(self):
        self.student_options = student_service.get_student_options(self.db)
        labels = [label for (_id, label) in self.student_options]
        self.student_combo["values"] = labels

    def _student_id_from_label(self, label):
        for student_id, opt_label in self.student_options:
            if opt_label == label:
                return student_id
        return None

    def _handle_load(self):
        student_id = self._student_id_from_label(
            self.student_var.get()
        )

        year = self.year_var.get().strip()

        if student_id is None:
            messagebox.showwarning(
                "No Selection",
                "Select a student first."
            )
            return

        if not year:
            messagebox.showwarning(
                "Missing Year",
                "Enter an academic year."
            )
            return

        self.current_student_id = student_id
        self.current_year = year
        self.selected_payment_id = None

        PaymentsFrame._last_student_label = self.student_var.get()
        PaymentsFrame._last_year = year

        try:
            summary = payment_service.get_fee_summary(
                self.db,
                student_id,
                year
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not load fee summary:\n{e}"
            )
            return

        self.current_student_name = summary["student"]["full_name"]

        self._render_summary(summary)
        self._refresh_monthly_breakdown(
            summary["fee_defined"]
        )
        self._refresh_history()

    def _refresh_history(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        if self.current_student_id is None or self.current_year is None:
            return

        payments = payment_service.get_payments_for_student(
            self.db,
            self.current_student_id,
            self.current_year
        )

        for p in payments:
            month_display = (
                p["month"]
                if "month" in p.keys() and p["month"]
                else "-"
            )

            self.tree.insert(
                "",
                "end",
                values=(
                    self.current_student_name or "",
                    month_display,
                    p["payment_date"],
                    f"{p['amount']:,.0f}",
                    p["note"] or "",
                    p["received_by"] or "",
                    p["id"],
                )
            )

    def _handle_row_select(self, event):
        selection = self.tree.selection()

        if not selection:
            self.selected_payment_id = None
            return

        item = self.tree.item(selection[0])
        values = item["values"]

        id_index = self.tree["columns"].index("id")

        self.selected_payment_id = values[id_index]

    # ------------------------------------------------------------------
    # Save / Delete payment
    # ------------------------------------------------------------------

    def _handle_save_payment(self):
        if self.current_student_id is None or self.current_year is None:
            messagebox.showwarning(
                "No Student Loaded",
                "Select a student and academic year, then click Load, before recording a payment."
            )
            return

        try:
            payment_service.add_payment(
                self.db,
                self.current_student_id,
                self.amount_var.get(),
                self.date_var.get(),
                self.current_year,
                self.month_var.get(),
                self.note_var.get(),
                self.received_by_var.get(),
                allow_overpayment=self.allow_overpay_var.get(),
            )
        except ValueError as e:
            messagebox.showwarning(
                "Cannot Save Payment",
                str(e)
            )
            return
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not save payment:\n{e}"
            )
            return

        messagebox.showinfo(
            "Saved",
            "Payment recorded successfully."
        )

        self.amount_var.set("")
        self.note_var.set("")
        self.allow_overpay_var.set(False)

        summary = payment_service.get_fee_summary(
            self.db,
            self.current_student_id,
            self.current_year
        )

        self._render_summary(summary)
        self._refresh_monthly_breakdown(
            summary["fee_defined"]
        )
        self._refresh_history()

    def _handle_delete_payment(self):
        if not check_owner_action(
            self.current_user,
            "حذف رکورد پرداخت / Deleting a payment record"
        ):
            return

        if self.selected_payment_id is None:
            messagebox.showwarning(
                "No Selection",
                "Select a payment from the history list first."
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this payment record?\n"
            "This cannot be undone."
        )

        if not confirm:
            return

        try:
            payment_service.delete_payment(
                self.db,
                self.selected_payment_id
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not delete payment:\n{e}"
            )
            return

        messagebox.showinfo(
            "Deleted",
            "Payment deleted."
        )

        self.selected_payment_id = None

        summary = payment_service.get_fee_summary(
            self.db,
            self.current_student_id,
            self.current_year
        )

        self._render_summary(summary)
        self._refresh_monthly_breakdown(
            summary["fee_defined"]
        )
        self._refresh_history()

    # ------------------------------------------------------------------
    # Print receipt
    # ------------------------------------------------------------------

    def _handle_print_receipt(self):
        if self.selected_payment_id is None:
            messagebox.showwarning(
                "No Selection",
                "Select a payment from the history list first, then click Print Receipt."
            )
            return

        try:
            file_path = receipt_service.save_and_open_receipt(
                self.db,
                self.selected_payment_id
            )
        except ValueError as e:
            messagebox.showwarning(
                "Cannot Generate Receipt",
                str(e)
            )
            return
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not generate receipt:\n{e}"
            )
            return

        messagebox.showinfo(
            "Receipt Generated",
            f"Receipt opened in your browser.\n\nSaved at:\n{file_path}"
        )