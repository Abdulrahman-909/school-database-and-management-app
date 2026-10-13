"""
ui/excel_export.py

Excel Export module: three buttons, each generating one report via
services/excel_export_service.py and opening it automatically.
No UI-level calculation happens here.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from services import excel_export_service


class ExcelExportFrame(ttk.Frame):
    def __init__(self, parent, db, on_back):
        super().__init__(parent, padding=20)
        self.db = db
        self.on_back = on_back

        self.pack(fill="both", expand=True)

        self._build_header()
        self._build_content()

    def _build_header(self):
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 20))

        ttk.Button(header, text="< بازگشت / Back", command=self.on_back).pack(side="left")

        ttk.Label(
            header, text="برامد اکسل / Excel Export",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=15)

    def _build_content(self):
        # --- Fee report (needs an academic year) ---
        fee_frame = ttk.LabelFrame(self, text="گزارش فیس شاگردان / Students Fee Report", padding=15)
        fee_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(fee_frame, text="سال تعلیمی / Academic Year:").pack(side="left", padx=(0, 5))
        self.year_var = tk.StringVar(value=str(date.today().year))
        ttk.Entry(fee_frame, textvariable=self.year_var, width=15).pack(side="left", padx=5)

        ttk.Button(
            fee_frame, text="ایجاد و بازکردن / Generate & Open",
            command=self._handle_export_fee_report
        ).pack(side="left", padx=15)

        ttk.Label(
            fee_frame,
            text="شامل: نام شاگرد، صنف، قابل پرداخت، پرداخت شده، باقی مانده\n"
                 "Includes: Student, Class, Total Fee, Paid, Remaining",
            font=("Segoe UI", 8, "italic"), foreground="#666666"
        ).pack(anchor="w", pady=(8, 0))

        # --- Financial summary ---
        fin_frame = ttk.LabelFrame(self, text="خلص مالی / Financial Summary", padding=15)
        fin_frame.pack(fill="x", pady=(0, 15))

        ttk.Button(
            fin_frame, text="ایجاد و بازکردن / Generate & Open",
            command=self._handle_export_financial_summary
        ).pack(side="left")

        ttk.Label(
            fin_frame,
            text="شامل: عواید، مصارف، معاشات و خالص عاید\n"
                 "Includes: Income, Expenses, Salaries, Net Income",
            font=("Segoe UI", 8, "italic"), foreground="#666666"
        ).pack(anchor="w", pady=(8, 0))

        # --- Student list ---
        student_frame = ttk.LabelFrame(self, text="لیست شاگردان / Student List", padding=15)
        student_frame.pack(fill="x", pady=(0, 15))

        ttk.Button(
            student_frame, text="ایجاد و بازکردن / Generate & Open",
            command=self._handle_export_student_list
        ).pack(side="left")

        ttk.Label(
            student_frame,
            text="شامل: نام، نام پدر، جنسیت، صنف، تلفن، وضعیت\n"
                 "Includes: Name, Father, Gender, Class, Phone, Status",
            font=("Segoe UI", 8, "italic"), foreground="#666666"
        ).pack(anchor="w", pady=(8, 0))

        ttk.Label(
            self,
            text="نوت: فایل‌ها در پوشه exports ذخیره و به صورت خودکار باز می‌شوند.\n"
                 "Note: files are saved in the exports folder and opened automatically.",
            font=("Segoe UI", 9), foreground="#888888"
        ).pack(anchor="w", pady=(10, 0))

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _handle_export_fee_report(self):
        try:
            file_path = excel_export_service.export_students_fee_report(self.db, self.year_var.get())
        except ValueError as e:
            messagebox.showwarning("Invalid Input", str(e))
            return
        except Exception as e:
            messagebox.showerror("Error", f"Could not generate report:\n{e}")
            return

        messagebox.showinfo("Report Generated", f"Saved and opened:\n{file_path}")

    def _handle_export_financial_summary(self):
        try:
            file_path = excel_export_service.export_financial_summary(self.db)
        except Exception as e:
            messagebox.showerror("Error", f"Could not generate report:\n{e}")
            return

        messagebox.showinfo("Report Generated", f"Saved and opened:\n{file_path}")

    def _handle_export_student_list(self):
        try:
            file_path = excel_export_service.export_student_list(self.db)
        except Exception as e:
            messagebox.showerror("Error", f"Could not generate report:\n{e}")
            return

        messagebox.showinfo("Report Generated", f"Saved and opened:\n{file_path}")