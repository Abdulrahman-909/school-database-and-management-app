"""
ui/students.py

Students module: Add / Edit / Delete / Search / Refresh.
Wrapped in a scrollable container so the form and list are reachable
even with many students and a small window.
All database access goes through services/student_service.py.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from services import student_service
from ui.scrollable import ScrollableFrame


GENDER_OPTIONS = ["ذکور / Male", "اناث / Female"]
STATUS_OPTIONS = ["active", "inactive", "graduated", "transferred"]


class StudentsFrame(ttk.Frame):
    def __init__(self, parent, db, on_back):
        super().__init__(parent, padding=0)
        self.db = db
        self.on_back = on_back

        self.selected_student_id = None
        self.class_options = []

        self.pack(fill="both", expand=True)

        scrollable = ScrollableFrame(self)
        scrollable.pack(fill="both", expand=True)
        self.body = scrollable.body

        self._build_header()
        self._build_form()
        self._build_search_and_list()

        self.refresh_list()

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _build_header(self):
        header = ttk.Frame(self.body)
        header.pack(fill="x", padx=15, pady=(15, 10))

        ttk.Button(
            header,
            text="< بازگشت / Back",
            command=self.on_back
        ).pack(side="left")

        ttk.Label(
            header,
            text="شاگردان / Students",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=15)

    # ------------------------------------------------------------------
    # Form
    # ------------------------------------------------------------------

    def _build_form(self):
        form = ttk.LabelFrame(
            self.body,
            text="افزودن / ویرایش شاگرد - Add / Edit Student",
            padding=15
        )
        form.pack(fill="x", padx=15, pady=(0, 10))

        self.full_name_var = tk.StringVar()
        self.father_name_var = tk.StringVar()
        self.gender_var = tk.StringVar()
        self.class_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.admission_date_var = tk.StringVar()
        self.status_var = tk.StringVar(value="active")
        self.custom_fee_var = tk.StringVar()

        ttk.Label(
            form,
            text="نام / Name:"
        ).grid(row=0, column=0, sticky="e", padx=5, pady=5)

        ttk.Entry(
            form,
            textvariable=self.full_name_var,
            width=25
        ).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(
            form,
            text="نام پدر / Father:"
        ).grid(row=0, column=2, sticky="e", padx=5, pady=5)

        ttk.Entry(
            form,
            textvariable=self.father_name_var,
            width=25
        ).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(
            form,
            text="جنسیت / Gender:"
        ).grid(row=1, column=0, sticky="e", padx=5, pady=5)

        ttk.Combobox(
            form,
            textvariable=self.gender_var,
            values=GENDER_OPTIONS,
            state="readonly",
            width=22
        ).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(
            form,
            text="صنف / Class:"
        ).grid(row=1, column=2, sticky="e", padx=5, pady=5)

        self.class_combo = ttk.Combobox(
            form,
            textvariable=self.class_var,
            values=[],
            state="readonly",
            width=22
        )

        self.class_combo.grid(
            row=1,
            column=3,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="تلفن / Phone:"
        ).grid(row=2, column=0, sticky="e", padx=5, pady=5)

        ttk.Entry(
            form,
            textvariable=self.phone_var,
            width=25
        ).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(
            form,
            text="آدرس / Address:"
        ).grid(row=2, column=2, sticky="e", padx=5, pady=5)

        ttk.Entry(
            form,
            textvariable=self.address_var,
            width=25
        ).grid(row=2, column=3, padx=5, pady=5)

        ttk.Label(
            form,
            text="تاریخ ثبت‌نام / Admission Date:"
        ).grid(row=3, column=0, sticky="e", padx=5, pady=5)

        date_entry = ttk.Entry(
            form,
            textvariable=self.admission_date_var,
            width=25
        )

        date_entry.grid(
            row=3,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="(YYYY-MM-DD)",
            font=("Segoe UI", 8),
            foreground="#888"
        ).grid(
            row=3,
            column=1,
            sticky="e",
            padx=(0, 60)
        )

        ttk.Label(
            form,
            text="وضعیت / Status:"
        ).grid(row=3, column=2, sticky="e", padx=5, pady=5)

        ttk.Combobox(
            form,
            textvariable=self.status_var,
            values=STATUS_OPTIONS,
            state="readonly",
            width=22
        ).grid(row=3, column=3, padx=5, pady=5)

        ttk.Label(
            form,
            text="فیس اختصاصی ماهانه / Custom Monthly Fee:"
        ).grid(row=4, column=0, sticky="e", padx=5, pady=5)

        ttk.Entry(
            form,
            textvariable=self.custom_fee_var,
            width=25
        ).grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(
            form,
            text="(خالی = فیس معمولی صنف / blank = normal class fee)",
            font=("Segoe UI", 8),
            foreground="#888"
        ).grid(row=4, column=2, columnspan=2, sticky="w", padx=5, pady=5)

        btn_frame = ttk.Frame(form)

        btn_frame.grid(
            row=5,
            column=0,
            columnspan=4,
            pady=(15, 0)
        )

        ttk.Button(
            btn_frame,
            text="ذخیره / Save",
            command=self._handle_save
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="پاک کردن فورم / Clear Form",
            command=self._clear_form
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="حذف / Delete",
            command=self._handle_delete
        ).pack(side="left", padx=5)

    # ------------------------------------------------------------------
    # Search + List
    # ------------------------------------------------------------------

    def _build_search_and_list(self):
        search_frame = ttk.Frame(self.body)
        search_frame.pack(
            fill="x",
            padx=15,
            pady=(5, 5)
        )

        ttk.Label(
            search_frame,
            text="جستجو / Search:"
        ).pack(side="left", padx=(0, 5))

        self.search_var = tk.StringVar()

        search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=30
        )

        search_entry.pack(
            side="left",
            padx=5
        )

        search_entry.bind(
            "<Return>",
            lambda e: self.refresh_list()
        )

        ttk.Button(
            search_frame,
            text="جستجو / Search",
            command=self.refresh_list
        ).pack(side="left", padx=5)

        ttk.Button(
            search_frame,
            text="تازه‌سازی / Refresh",
            command=self._handle_refresh
        ).pack(side="left", padx=5)

        columns = (
            "id",
            "full_name",
            "father_name",
            "gender",
            "class",
            "phone",
            "status"
        )

        # --------------------------------------------------------------
        # This list keeps its OWN vertical scrollbar for the Treeview
        # rows (unrelated to the whole-page ScrollableFrame above -
        # both work independently and don't conflict).
        # --------------------------------------------------------------

        list_frame = ttk.Frame(self.body)

        list_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(5, 15)
        )

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=20
        )

        headings = {
            "id": "ID",
            "full_name": "نام / Name",
            "father_name": "نام پدر / Father",
            "gender": "جنسیت / Gender",
            "class": "صنف / Class",
            "phone": "تلفن / Phone",
            "status": "وضعیت / Status",
        }

        widths = {
            "id": 50,
            "full_name": 160,
            "father_name": 140,
            "gender": 90,
            "class": 120,
            "phone": 110,
            "status": 90
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

        # Treeview fills the list area
        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        # Scrollbar ONLY for the student list
        table_scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview
        )

        table_scrollbar.pack(
            side="right",
            fill="y"
        )

        self.tree.configure(
            yscrollcommand=table_scrollbar.set
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self._handle_row_select
        )

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def refresh_list(self):
        self._load_class_options()

        for row in self.tree.get_children():
            self.tree.delete(row)

        search_text = self.search_var.get().strip()

        students = student_service.get_all_students(
            self.db,
            search_text
        )

        for s in students:
            class_display = (
                s["class_name"]
                if s["class_name"]
                else "-"
            )

            if s["class_name"] and s["class_section"]:
                class_display = (
                    f"{s['class_name']} - "
                    f"{s['class_section']}"
                )

            self.tree.insert(
                "",
                "end",
                values=(
                    s["id"],
                    s["full_name"],
                    s["father_name"] or "",
                    s["gender"] or "",
                    class_display,
                    s["phone"] or "",
                    s["status"]
                )
            )

    def _handle_refresh(self):
        self.search_var.set("")
        self._clear_form()
        self.refresh_list()

    # ------------------------------------------------------------------
    # Class options
    # ------------------------------------------------------------------

    def _load_class_options(self):
        self.class_options = student_service.get_class_options(
            self.db
        )

        labels = [
            label
            for (_id, label) in self.class_options
        ]

        self.class_combo["values"] = labels

        if not labels:
            self.class_combo.set("")

    def _class_id_from_label(self, label):
        for class_id, opt_label in self.class_options:
            if opt_label == label:
                return class_id

        return None

    def _class_label_from_id(self, class_id):
        for opt_id, label in self.class_options:
            if opt_id == class_id:
                return label

        return ""

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def _handle_row_select(self, event):
        selection = self.tree.selection()

        if not selection:
            return

        item = self.tree.item(selection[0])
        student_id = item["values"][0]

        student = student_service.get_student_by_id(
            self.db,
            student_id
        )

        if student is None:
            return

        self.selected_student_id = student["id"]

        self.full_name_var.set(
            student["full_name"] or ""
        )

        self.father_name_var.set(
            student["father_name"] or ""
        )

        self.gender_var.set(
            student["gender"] or ""
        )

        self.class_var.set(
            self._class_label_from_id(
                student["class_id"]
            )
        )

        self.phone_var.set(
            student["phone"] or ""
        )

        self.address_var.set(
            student["address"] or ""
        )
        self.admission_date_var.set(
            student["admission_date"] or ""
        )

        self.status_var.set(
            student["status"] or "active"
        )

        custom_fee = student["custom_monthly_fee"] if "custom_monthly_fee" in student.keys() else None
        self.custom_fee_var.set(str(custom_fee) if custom_fee is not None else "")

    def _clear_form(self):
        self.selected_student_id = None

        self.full_name_var.set("")
        self.father_name_var.set("")
        self.gender_var.set("")
        self.class_var.set("")
        self.phone_var.set("")
        self.address_var.set("")
        self.admission_date_var.set("")
        self.status_var.set("active")
        self.custom_fee_var.set("")

        self.tree.selection_remove(
            self.tree.selection()
        )

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def _handle_save(self):
        class_id = self._class_id_from_label(
            self.class_var.get()
        )

        try:
            if self.selected_student_id is None:
                student_service.add_student(
                    self.db,
                    self.full_name_var.get(),
                    self.father_name_var.get(),
                    self.gender_var.get(),
                    class_id,
                    self.phone_var.get(),
                    self.address_var.get(),
                    self.admission_date_var.get(),
                    self.status_var.get(),
                    self.custom_fee_var.get(),
                )

                messagebox.showinfo(
                    "Saved",
                    "Student added successfully."
                )

            else:
                student_service.update_student(
                    self.db,
                    self.selected_student_id,
                    self.full_name_var.get(),
                    self.father_name_var.get(),
                    self.gender_var.get(),
                    class_id,
                    self.phone_var.get(),
                    self.address_var.get(),
                    self.admission_date_var.get(),
                    self.status_var.get(),
                    self.custom_fee_var.get(),
                )

                messagebox.showinfo(
                    "Saved",
                    "Student updated successfully."
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
                f"Could not save student:\n{e}"
            )
            return

        self._clear_form()
        self.refresh_list()

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def _handle_delete(self):
        if self.selected_student_id is None:
            messagebox.showwarning(
                "No Selection",
                "Select a student from the list first."
            )
            return

        name = self.full_name_var.get()

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{name}'?\n"
            "This cannot be undone."
        )

        if not confirm:
            return

        try:
            student_service.delete_student(
                self.db,
                self.selected_student_id
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
                f"Could not delete student:\n{e}"
            )
            return

        messagebox.showinfo(
            "Deleted",
            "Student deleted."
        )

        self._clear_form()
        self.refresh_list()