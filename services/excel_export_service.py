"""
services/excel_export_service.py

Generates Excel (.xlsx) reports using openpyxl. Every number here comes
from the SAME service functions already used by ui/reports.py and
ui/payments.py - this file does not recalculate fee totals, income,
expenses, or salaries on its own. In particular, "Total Fee" and
"Remaining" always come from payment_service.get_fee_summary()
(Total Fee - Total Paid), never from summing payment rows directly,
per the project's core fee-accuracy rule.
"""

import os
from pathlib import Path
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

from services import student_service
from services import payment_service
from services import class_service
from services import finance_service
from services import salary_service


HEADER_FILL = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
HEADER_FONT = Font(color="FFFFFF", bold=True)


def _get_exports_dir() -> Path:
    project_root = Path(__file__).resolve().parent.parent
    exports_dir = project_root / "exports"
    exports_dir.mkdir(exist_ok=True)
    return exports_dir


def _style_header_row(ws, row_num, num_columns):
    for col in range(1, num_columns + 1):
        cell = ws.cell(row=row_num, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")


def _autosize_columns(ws, num_columns):
    """
    Widens each column to fit its longest value. Uses get_column_letter()
    directly (not cell.column_letter) because row 1 contains a merged
    title cell - the non-top-left cells in a merged range are
    MergedCell objects, which don't support .column_letter.
    """
    for col in range(1, num_columns + 1):
        col_letter = get_column_letter(col)
        max_len = 10
        for row in ws.iter_rows(min_col=col, max_col=col):
            for cell in row:
                if cell.value is not None:
                    max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max_len + 3, 45)


def _open_file(path: Path):
    try:
        os.startfile(str(path))  # Windows only, matches this project's target platform
    except AttributeError:
        # Not on Windows (e.g. testing on Mac/Linux) - just skip auto-open.
        pass


# ----------------------------------------------------------------------
# Report 1: Students Fee Report
# ----------------------------------------------------------------------

def export_students_fee_report(db, academic_year: str) -> str:
    """
    Student, Total Fee, Total Paid, Remaining - for the given academic
    year. Uses payment_service.get_fee_summary() per student (never a
    raw SUM of payments), matching spec Section 17 exactly.
    """
    if not academic_year or not str(academic_year).strip():
        raise ValueError("Academic year is required.")
    academic_year = str(academic_year).strip()

    wb = Workbook()
    ws = wb.active
    ws.title = "Fee Report"
    ws.sheet_view.rightToLeft = True

    ws.cell(row=1, column=1, value=f"گزارش فیس شاگردان / Students Fee Report - {academic_year}")
    ws.cell(row=1, column=1).font = Font(bold=True, size=14)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=6)

    headers = ["شاگرد / Student", "صنف / Class", "قابل پرداخت / Total Fee",
               "پرداخت شده / Paid", "باقی مانده / Remaining", "وضعیت / Status"]
    header_row = 3
    for i, h in enumerate(headers, start=1):
        ws.cell(row=header_row, column=i, value=h)
    _style_header_row(ws, header_row, len(headers))

    students = student_service.get_all_students(db)
    row_num = header_row + 1

    for s in students:
        if s["status"] != "active":
            continue

        summary = payment_service.get_fee_summary(db, s["id"], academic_year)

        class_label = "-"
        if s["class_id"] is not None:
            class_row = class_service.get_class_by_id(db, s["class_id"])
            if class_row:
                class_label = class_row["name"]
                if class_row["section"]:
                    class_label += f" - {class_row['section']}"

        if not summary["fee_defined"]:
            status = "فیس تعریف نشده / No fee set"
            total_fee_display = "-"
        elif summary["remaining"] <= 0:
            status = "پرداخت شده / Paid"
            total_fee_display = summary["total_fee"]
        else:
            status = "باقی مانده / Remaining"
            total_fee_display = summary["total_fee"]

        ws.cell(row=row_num, column=1, value=s["full_name"])
        ws.cell(row=row_num, column=2, value=class_label)
        ws.cell(row=row_num, column=3, value=total_fee_display)
        ws.cell(row=row_num, column=4, value=summary["total_paid"])
        ws.cell(row=row_num, column=5, value=summary["remaining"] if summary["fee_defined"] else "-")
        ws.cell(row=row_num, column=6, value=status)
        row_num += 1

    _autosize_columns(ws, len(headers))

    exports_dir = _get_exports_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = exports_dir / f"Fee_Report_{academic_year}_{timestamp}.xlsx"
    wb.save(file_path)

    _open_file(file_path)
    return str(file_path)


# ----------------------------------------------------------------------
# Report 2: Financial Summary
# ----------------------------------------------------------------------

def export_financial_summary(db) -> str:
    """
    Same combined Income/Expenses/Salaries/Net Income numbers as the
    Reports > Financial Summary tab - reusing the exact same service
    calls, not recalculated here.
    """
    fees_collected = payment_service.get_total_paid_all_students(db)
    other_income = finance_service.get_total_income(db)
    total_income = fees_collected + other_income

    direct_expenses = finance_service.get_total_expenses(db)
    salaries_paid = salary_service.get_total_salaries_paid(db)
    total_expenses = direct_expenses + salaries_paid

    net_income = total_income - total_expenses

    wb = Workbook()
    ws = wb.active
    ws.title = "Financial Summary"
    ws.sheet_view.rightToLeft = True

    ws.cell(row=1, column=1, value="خلص مالی / Financial Summary")
    ws.cell(row=1, column=1).font = Font(bold=True, size=14)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=2)

    rows = [
        ("عواید / INCOME", ""),
        ("مجموع فیس دریافت شده / Total Fees Collected", fees_collected),
        ("مجموع سایر عواید / Total Other Income", other_income),
        ("مجموع عواید کل / Total Income (Combined)", total_income),
        ("", ""),
        ("مصارف / EXPENSES", ""),
        ("مصارف مستقیم / Direct Expenses", direct_expenses),
        ("مجموع معاشات / Total Salaries Paid", salaries_paid),
        ("مجموع مصارف کل / Total Expenses (Combined)", total_expenses),
        ("", ""),
        ("خالص عاید / NET INCOME", net_income),
    ]

    header_row = 3
    ws.cell(row=header_row, column=1, value="شرح / Description")
    ws.cell(row=header_row, column=2, value="مبلغ / Amount")
    _style_header_row(ws, header_row, 2)

    row_num = header_row + 1
    for label, value in rows:
        ws.cell(row=row_num, column=1, value=label)
        if value != "":
            ws.cell(row=row_num, column=2, value=value)
        if label in ("عواید / INCOME", "مصارف / EXPENSES", "خالص عاید / NET INCOME"):
            ws.cell(row=row_num, column=1).font = Font(bold=True)
            ws.cell(row=row_num, column=2).font = Font(bold=True)
        row_num += 1

    _autosize_columns(ws, 2)

    exports_dir = _get_exports_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = exports_dir / f"Financial_Summary_{timestamp}.xlsx"
    wb.save(file_path)

    _open_file(file_path)
    return str(file_path)


# ----------------------------------------------------------------------
# Report 3: Full Student List
# ----------------------------------------------------------------------

def export_student_list(db) -> str:
    """
    General roster - no fee numbers here (that's the Fee Report above),
    just the student directory.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Students"
    ws.sheet_view.rightToLeft = True

    ws.cell(row=1, column=1, value="لیست شاگردان / Student List")
    ws.cell(row=1, column=1).font = Font(bold=True, size=14)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=6)

    headers = ["نام / Name", "نام پدر / Father", "جنسیت / Gender",
               "صنف / Class", "تلفن / Phone", "وضعیت / Status"]
    header_row = 3
    for i, h in enumerate(headers, start=1):
        ws.cell(row=header_row, column=i, value=h)
    _style_header_row(ws, header_row, len(headers))

    students = student_service.get_all_students(db)
    row_num = header_row + 1

    for s in students:
        class_label = "-"
        if s["class_name"]:
            class_label = s["class_name"]
            if s["class_section"]:
                class_label += f" - {s['class_section']}"

        ws.cell(row=row_num, column=1, value=s["full_name"])
        ws.cell(row=row_num, column=2, value=s["father_name"] or "")
        ws.cell(row=row_num, column=3, value=s["gender"] or "")
        ws.cell(row=row_num, column=4, value=class_label)
        ws.cell(row=row_num, column=5, value=s["phone"] or "")
        ws.cell(row=row_num, column=6, value=s["status"])
        row_num += 1

    _autosize_columns(ws, len(headers))

    exports_dir = _get_exports_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = exports_dir / f"Student_List_{timestamp}.xlsx"
    wb.save(file_path)

    _open_file(file_path)
    return str(file_path)