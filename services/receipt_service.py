"""
services/receipt_service.py

Generates a printable HTML payment receipt for a single payment record,
saves it into exports/receipts/, and opens it in the default web
browser. Printing/saving as PDF is done by the user via the browser's
own Ctrl+P - no PDF library needed.

All numbers here come from services/payment_service.py and
services/student_service.py - this file does no fee math of its own,
so the receipt can never disagree with what the Payments screen shows.
"""

import os
import webbrowser
from pathlib import Path
from datetime import datetime

from services import payment_service
from services import student_service
from services import class_service


# Edit this if the school's name changes. Not worth a full settings
# system for a single string at this stage.
SCHOOL_NAME = "مکتب خصوصی - Private School"


def _get_exports_dir() -> Path:
    project_root = Path(__file__).resolve().parent.parent
    receipts_dir = project_root / "exports" / "receipts"
    receipts_dir.mkdir(parents=True, exist_ok=True)
    return receipts_dir


def build_receipt_data(db, payment_id: int) -> dict:
    """
    Gathers everything needed for the receipt. Raises ValueError with a
    clear message if the payment can't be found.
    """
    payment = payment_service.get_payment_by_id(db, payment_id)
    if payment is None:
        raise ValueError("Payment record not found.")

    student = student_service.get_student_by_id(db, payment["student_id"])
    if student is None:
        raise ValueError("The student for this payment could not be found.")

    class_label = "-"
    if student["class_id"] is not None:
        class_row = class_service.get_class_by_id(db, student["class_id"])
        if class_row:
            class_label = class_row["name"]
            if class_row["section"]:
                class_label += f" - {class_row['section']}"

    academic_year = payment["academic_year"]
    summary = payment_service.get_fee_summary(db, student["id"], academic_year)

    # "Previously paid" = everything for this student+year recorded
    # BEFORE this specific payment (lower id = recorded earlier).
    all_payments = payment_service.get_payments_for_student(db, student["id"], academic_year)
    previously_paid = sum(
        p["amount"] for p in all_payments if p["id"] < payment["id"]
    )
    current_payment = payment["amount"]
    total_paid_after = previously_paid + current_payment
    remaining_after = summary["total_fee"] - total_paid_after if summary["fee_defined"] else None

    return {
        "receipt_number": f"RCT-{payment['id']:05d}",
        "school_name": SCHOOL_NAME,
        "student_id_display": f"STU-{student['id']:04d}",
        "student_name": student["full_name"],
        "class_label": class_label,
        "academic_year": academic_year,
        "total_fee": summary["total_fee"] if summary["fee_defined"] else None,
        "previously_paid": previously_paid,
        "current_payment": current_payment,
        "total_paid_after": total_paid_after,
        "remaining_after": remaining_after,
        "payment_date": payment["payment_date"],
        "received_by": payment["received_by"] or "-",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def _fmt(value):
    if value is None:
        return "تعریف نشده / Not set"
    return f"{value:,.0f}"


def generate_receipt_html(data: dict) -> str:
    remaining_display = _fmt(data["remaining_after"])
    remaining_color = "#166534" if (data["remaining_after"] or 0) <= 0 else "#b91c1c"

    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<title>رسید پرداخت / Payment Receipt - {data['receipt_number']}</title>
<style>
    body {{
        font-family: Tahoma, "Segoe UI", sans-serif;
        background: #f0f0f0;
        margin: 0;
        padding: 20px;
    }}
    .receipt {{
        max-width: 650px;
        margin: 0 auto;
        background: white;
        padding: 35px;
        border: 1px solid #ccc;
        border-radius: 6px;
    }}
    .school-name {{
        text-align: center;
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 4px;
    }}
    .receipt-title {{
        text-align: center;
        font-size: 16px;
        color: #555;
        margin-bottom: 20px;
        border-bottom: 2px solid #333;
        padding-bottom: 15px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }}
    td {{
        padding: 8px 6px;
        border-bottom: 1px solid #eee;
        font-size: 14px;
    }}
    td.label {{
        font-weight: bold;
        color: #333;
        width: 45%;
    }}
    tr.highlight td {{
        font-weight: bold;
        font-size: 15px;
        color: {remaining_color};
        border-top: 2px solid #333;
        border-bottom: none;
    }}
    .signature-area {{
        margin-top: 40px;
        display: flex;
        justify-content: space-between;
    }}
    .signature-box {{
        text-align: center;
        width: 45%;
    }}
    .signature-line {{
        margin-top: 40px;
        border-top: 1px solid #333;
        padding-top: 5px;
        font-size: 13px;
    }}
    .print-btn {{
        display: block;
        margin: 20px auto 0 auto;
        padding: 10px 25px;
        font-size: 14px;
        cursor: pointer;
    }}
    .footer-note {{
        text-align: center;
        font-size: 11px;
        color: #999;
        margin-top: 25px;
    }}
    @media print {{
        body {{ background: white; padding: 0; }}
        .receipt {{ border: none; }}
        .print-btn {{ display: none; }}
    }}
</style>
</head>
<body>
    <div class="receipt">
        <div class="school-name">{data['school_name']}</div>
        <div class="receipt-title">رسید پرداخت فیس / Payment Receipt</div>

        <table>
            <tr><td class="label">شماره رسید / Receipt Number</td><td>{data['receipt_number']}</td></tr>
            <tr><td class="label">تاریخ پرداخت / Payment Date</td><td>{data['payment_date']}</td></tr>
            <tr><td class="label">شماره شاگرد / Student ID</td><td>{data['student_id_display']}</td></tr>
            <tr><td class="label">نام شاگرد / Student Name</td><td>{data['student_name']}</td></tr>
            <tr><td class="label">صنف / Class</td><td>{data['class_label']}</td></tr>
            <tr><td class="label">سال تعلیمی / Academic Year</td><td>{data['academic_year']}</td></tr>
            <tr><td class="label">مجموع فیس / Total Fee</td><td>{_fmt(data['total_fee'])}</td></tr>
            <tr><td class="label">پرداخت شده قبلی / Previously Paid</td><td>{_fmt(data['previously_paid'])}</td></tr>
            <tr><td class="label">پرداخت فعلی / Current Payment</td><td>{_fmt(data['current_payment'])}</td></tr>
            <tr><td class="label">مجموع پرداخت شده / Total Paid</td><td>{_fmt(data['total_paid_after'])}</td></tr>
            <tr class="highlight"><td class="label">باقی مانده / Remaining</td><td>{remaining_display}</td></tr>
            <tr><td class="label">دریافت کننده / Received By</td><td>{data['received_by']}</td></tr>
        </table>

        <div class="signature-area">
            <div class="signature-box">
                <div class="signature-line">امضاء دریافت کننده / Received By Signature</div>
            </div>
            <div class="signature-box">
                <div class="signature-line">مهر مکتب / School Stamp</div>
            </div>
        </div>

        <div class="footer-note">Generated {data['generated_at']}</div>

        <button class="print-btn" onclick="window.print()">چاپ / Print</button>
    </div>
</body>
</html>
"""


def save_and_open_receipt(db, payment_id: int) -> str:
    """
    Builds the receipt, writes it to exports/receipts/, opens it in the
    default browser, and returns the file path. Raises ValueError if
    the payment doesn't exist (caller should show this message to the user).
    """
    data = build_receipt_data(db, payment_id)
    html = generate_receipt_html(data)

    receipts_dir = _get_exports_dir()
    file_path = receipts_dir / f"{data['receipt_number']}.html"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)

    webbrowser.open(f"file://{file_path.resolve()}")

    return str(file_path)
def build_course_receipt_data(db, course_payment_id: int) -> dict:
    """
    Same idea as build_receipt_data(), but for a Winter Course student
    payment - different fields (course, course student, no academic
    year/class) since course_payments is a completely separate table
    from the school's own payments.
    """
    from services import course_service
    from services import course_payment_service

    payment = db.fetchone("SELECT * FROM course_payments WHERE id = ?;", (course_payment_id,))
    if payment is None:
        raise ValueError("Course payment record not found.")

    enrollment = course_service.get_enrollment_by_id(db, payment["enrollment_id"])
    if enrollment is None:
        raise ValueError("Enrollment for this payment could not be found.")

    course = course_service.get_course_by_id(db, enrollment["course_id"])
    student = course_service.get_course_student_by_id(db, enrollment["course_student_id"])

    all_payments = course_payment_service.get_payments_for_enrollment(db, enrollment["id"])
    previously_paid = sum(p["amount"] for p in all_payments if p["id"] < payment["id"])
    current_payment = payment["amount"]
    total_paid_after = previously_paid + current_payment
    remaining_after = enrollment["fee_amount"] - total_paid_after

    return {
        "receipt_number": f"CRCT-{payment['id']:05d}",
        "school_name": SCHOOL_NAME,
        "course_name": course["name"] if course else "-",
        "student_name": student["full_name"] if student else "-",
        "student_phone": (student["phone"] if student and student["phone"] else "-"),
        "total_fee": enrollment["fee_amount"],
        "previously_paid": previously_paid,
        "current_payment": current_payment,
        "total_paid_after": total_paid_after,
        "remaining_after": remaining_after,
        "payment_date": payment["payment_date"],
        "note": payment["note"] or "-",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def generate_course_receipt_html(data: dict) -> str:
    remaining_color = "#166534" if data["remaining_after"] <= 0 else "#b91c1c"

    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<title>رسید پرداخت دوره / Course Payment Receipt - {data['receipt_number']}</title>
<style>
    body {{ font-family: Tahoma, "Segoe UI", sans-serif; background: #f0f0f0; margin: 0; padding: 20px; }}
    .receipt {{ max-width: 650px; margin: 0 auto; background: white; padding: 35px; border: 1px solid #ccc; border-radius: 6px; }}
    .school-name {{ text-align: center; font-size: 22px; font-weight: bold; margin-bottom: 4px; }}
    .receipt-title {{ text-align: center; font-size: 16px; color: #555; margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 15px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    td {{ padding: 8px 6px; border-bottom: 1px solid #eee; font-size: 14px; }}
    td.label {{ font-weight: bold; color: #333; width: 45%; }}
    tr.highlight td {{ font-weight: bold; font-size: 15px; color: {remaining_color}; border-top: 2px solid #333; border-bottom: none; }}
    .signature-area {{ margin-top: 40px; display: flex; justify-content: space-between; }}
    .signature-box {{ text-align: center; width: 45%; }}
    .signature-line {{ margin-top: 40px; border-top: 1px solid #333; padding-top: 5px; font-size: 13px; }}
    .print-btn {{ display: block; margin: 20px auto 0 auto; padding: 10px 25px; font-size: 14px; cursor: pointer; }}
    .footer-note {{ text-align: center; font-size: 11px; color: #999; margin-top: 25px; }}
    @media print {{ body {{ background: white; padding: 0; }} .receipt {{ border: none; }} .print-btn {{ display: none; }} }}
</style>
</head>
<body>
    <div class="receipt">
        <div class="school-name">{data['school_name']}</div>
        <div class="receipt-title">رسید پرداخت دوره زمستانی / Winter Course Payment Receipt</div>

        <table>
            <tr><td class="label">شماره رسید / Receipt Number</td><td>{data['receipt_number']}</td></tr>
            <tr><td class="label">تاریخ پرداخت / Payment Date</td><td>{data['payment_date']}</td></tr>
            <tr><td class="label">دوره / Course</td><td>{data['course_name']}</td></tr>
            <tr><td class="label">نام شاگرد / Student Name</td><td>{data['student_name']}</td></tr>
            <tr><td class="label">تلفن / Phone</td><td>{data['student_phone']}</td></tr>
            <tr><td class="label">فیس دوره / Course Fee</td><td>{data['total_fee']:,.0f}</td></tr>
            <tr><td class="label">پرداخت شده قبلی / Previously Paid</td><td>{data['previously_paid']:,.0f}</td></tr>
            <tr><td class="label">پرداخت فعلی / Current Payment</td><td>{data['current_payment']:,.0f}</td></tr>
            <tr><td class="label">مجموع پرداخت شده / Total Paid</td><td>{data['total_paid_after']:,.0f}</td></tr>
            <tr class="highlight"><td class="label">باقی مانده / Remaining</td><td>{data['remaining_after']:,.0f}</td></tr>
            <tr><td class="label">یادداشت / Note</td><td>{data['note']}</td></tr>
        </table>

        <div class="signature-area">
            <div class="signature-box"><div class="signature-line">امضاء دریافت کننده / Received By Signature</div></div>
            <div class="signature-box"><div class="signature-line">مهر مکتب / School Stamp</div></div>
        </div>

        <div class="footer-note">Generated {data['generated_at']}</div>

        <button class="print-btn" onclick="window.print()">چاپ / Print</button>
    </div>
</body>
</html>
"""


def save_and_open_course_receipt(db, course_payment_id: int) -> str:
    """
    Same pattern as save_and_open_receipt(), for a Winter Course
    student payment instead of a school payment.
    """
    data = build_course_receipt_data(db, course_payment_id)
    html = generate_course_receipt_html(data)

    receipts_dir = _get_exports_dir()
    file_path = receipts_dir / f"{data['receipt_number']}.html"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)

    webbrowser.open(f"file://{file_path.resolve()}")

    return str(file_path)