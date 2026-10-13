"""
ui/teachers.py

Teachers module: Add / Edit / Delete / Search / Refresh.
All database access goes through services/teacher_service.py.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from services import teacher_service
from ui.scrollable import ScrollableFrame

STATUS_OPTIONS = ["active", "inactive"]


class TeachersFrame(ttk.Frame):
    def __init__(self, parent, db, on_back):
        super().__init__(parent, padding=15)
        self.db = db
        self.on_back = on_back

        self.selected_teacher_id = None

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
        header.pack(fill="x", pady=(0, 10))

        ttk.Button(
            header,
            text="< بازگشت / Back",
            command=self.on_back
        ).pack(side="left")

        ttk.Label(
            header,
            text="استادان / Teachers",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=15)

    # ------------------------------------------------------------------
    # Form
    # ------------------------------------------------------------------

    def _build_form(self):
        form = ttk.LabelFrame(
            self.body,
            text="افزودن / ویرایش استاد - Add / Edit Teacher",
            padding=15
        )
        form.pack(fill="x", pady=(0, 10))

        self.full_name_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.subject_var = tk.StringVar()
        self.salary_var = tk.StringVar()
        self.status_var = tk.StringVar(value="active")

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
            text="تلفن / Phone:"
        ).grid(row=0, column=2, sticky="e", padx=5, pady=5)

        ttk.Entry(
            form,
            textvariable=self.phone_var,
            width=25
        ).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(
            form,
            text="مضمون / Subject:"
        ).grid(row=1, column=0, sticky="e", padx=5, pady=5)

        ttk.Entry(
            form,
            textvariable=self.subject_var,
            width=25
        ).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(
            form,
            text="معاش اساسی / Salary:"
        ).grid(row=1, column=2, sticky="e", padx=5, pady=5)

        ttk.Entry(
            form,
            textvariable=self.salary_var,
            width=25
        ).grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(
            form,
            text="وضعیت / Status:"
        ).grid(row=2, column=0, sticky="e", padx=5, pady=5)

        ttk.Combobox(
            form,
            textvariable=self.status_var,
            values=STATUS_OPTIONS,
            state="readonly",
            width=22
        ).grid(row=2, column=1, padx=5, pady=5)

        btn_frame = ttk.Frame(form)

        btn_frame.grid(
            row=3,
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
            "subject",
            "phone",
            "salary",
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
            pady=(5, 15)
        )

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=15
        )

        headings = {
            "id": "ID",
            "full_name": "نام / Name",
            "subject": "مضمون / Subject",
            "phone": "تلفن / Phone",
            "salary": "معاش / Salary",
            "status": "وضعیت / Status",
        }

        widths = {
            "id": 50,
            "full_name": 180,
            "subject": 140,
            "phone": 120,
            "salary": 100,
            "status": 100
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

        # Scrollbar ONLY for the teacher list
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
        for row in self.tree.get_children():
            self.tree.delete(row)

        search_text = self.search_var.get().strip()

        teachers = teacher_service.get_all_teachers(
            self.db,
            search_text
        )

        for t in teachers:
            self.tree.insert(
                "",
                "end",
                values=(
                    t["id"],
                    t["full_name"],
                    t["subject"] or "",
                    t["phone"] or "",
                    f"{t['salary_amount']:,.0f}",
                    t["status"]
                )
            )

    def _handle_refresh(self):
        self.search_var.set("")
        self._clear_form()
        self.refresh_list()

    # ------------------------------------------------------------------
    # Form <-> selection
    # ------------------------------------------------------------------

    def _handle_row_select(self, event):
        selection = self.tree.selection()

        if not selection:
            return

        item = self.tree.item(selection[0])
        teacher_id = item["values"][0]

        teacher = teacher_service.get_teacher_by_id(
            self.db,
            teacher_id
        )

        if teacher is None:
            return

        self.selected_teacher_id = teacher["id"]

        self.full_name_var.set(
            teacher["full_name"] or ""
        )

        self.phone_var.set(
            teacher["phone"] or ""
        )

        self.subject_var.set(
            teacher["subject"] or ""
        )

        self.salary_var.set(
            str(teacher["salary_amount"])
        )

        self.status_var.set(
            teacher["status"] or "active"
        )

    def _clear_form(self):
        self.selected_teacher_id = None

        self.full_name_var.set("")
        self.phone_var.set("")
        self.subject_var.set("")
        self.salary_var.set("")
        self.status_var.set("active")

        self.tree.selection_remove(
            self.tree.selection()
        )

    # ------------------------------------------------------------------
    # Save / Delete
    # ------------------------------------------------------------------

    def _handle_save(self):
        try:
            if self.selected_teacher_id is None:
                teacher_service.add_teacher(
                    self.db,
                    self.full_name_var.get(),
                    self.phone_var.get(),
                    self.subject_var.get(),
                    self.salary_var.get(),
                    self.status_var.get(),
                )

                messagebox.showinfo(
                    "Saved",
                    "Teacher added successfully."
                )

            else:
                teacher_service.update_teacher(
                    self.db,
                    self.selected_teacher_id,
                    self.full_name_var.get(),
                    self.phone_var.get(),
                    self.subject_var.get(),
                    self.salary_var.get(),
                    self.status_var.get(),
                )

                messagebox.showinfo(
                    "Saved",
                    "Teacher updated successfully."
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
                f"Could not save teacher:\n{e}"
            )
            return

        self._clear_form()
        self.refresh_list()

    def _handle_delete(self):
        if self.selected_teacher_id is None:
            messagebox.showwarning(
                "No Selection",
                "Select a teacher from the list first."
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
            teacher_service.delete_teacher(
                self.db,
                self.selected_teacher_id
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not delete teacher:\n{e}"
            )
            return

        messagebox.showinfo(
            "Deleted",
            "Teacher deleted."
        )

        self._clear_form()
        self.refresh_list()