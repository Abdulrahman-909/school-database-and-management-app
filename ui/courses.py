"""
ui/courses.py

Winter Courses module:
- Course Teachers
- Courses
- Course Students
- Enrollments
- Course Details

Course Details includes:
- Student payments
- Teacher revenue share
- Teacher payouts

Deleting a student payment or teacher payout is restricted
to the school owner.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from services import course_service
from services import course_payment_service
from services import receipt_service
from services.permissions import check_owner_action


# ==========================================================================
# Scrollable Frame
# ==========================================================================

class ScrollableFrame(ttk.Frame):
    """
    A reusable vertically scrollable frame.
    Used by Course Details because that page contains many sections.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.canvas = tk.Canvas(
            self,
            borderwidth=0,
            highlightthickness=0
        )

        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )

        self.interior = ttk.Frame(self.canvas)

        self.window_id = self.canvas.create_window(
            (0, 0),
            window=self.interior,
            anchor="nw"
        )

        self.canvas.configure(
            yscrollcommand=self.scrollbar.set
        )

        self.interior.bind(
            "<Configure>",
            self._update_scrollregion
        )

        self.canvas.bind(
            "<Configure>",
            self._resize_interior
        )

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.scrollbar.pack(
            side="right",
            fill="y"
        )

        self.canvas.bind(
            "<Enter>",
            self._bind_mousewheel
        )

        self.canvas.bind(
            "<Leave>",
            self._unbind_mousewheel
        )

    def _update_scrollregion(self, event=None):
        self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        )

    def _resize_interior(self, event):
        self.canvas.itemconfigure(
            self.window_id,
            width=event.width
        )

    def _bind_mousewheel(self, event=None):
        self.canvas.bind_all(
            "<MouseWheel>",
            self._on_mousewheel
        )

    def _unbind_mousewheel(self, event=None):
        self.canvas.unbind_all(
            "<MouseWheel>"
        )

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units"
        )


# ==========================================================================
# Courses Main Frame
# ==========================================================================

class CoursesFrame(ttk.Frame):

    def __init__(self, parent, db, current_user, on_back):
        super().__init__(parent, padding=15)

        self.db = db
        self.current_user = current_user
        self.on_back = on_back

        self.pack(
            fill="both",
            expand=True
        )

        self._build_header()

        notebook = ttk.Notebook(self)

        notebook.pack(
            fill="both",
            expand=True,
            pady=(10, 0)
        )

        self.teachers_tab = CourseTeachersTab(
            notebook,
            db,
            on_change=self._on_any_change
        )

        self.courses_tab = CoursesTab(
            notebook,
            db,
            on_change=self._on_any_change
        )

        self.students_tab = CourseStudentsTab(
            notebook,
            db,
            on_change=self._on_any_change
        )

        self.enrollments_tab = EnrollmentsTab(
            notebook,
            db,
            on_change=self._on_any_change
        )

        self.details_tab = CourseDetailsTab(
            notebook,
            db,
            current_user
        )

        notebook.add(
            self.teachers_tab,
            text="استادان دوره / Course Teachers"
        )

        notebook.add(
            self.courses_tab,
            text="دوره‌ها / Courses"
        )

        notebook.add(
            self.students_tab,
            text="شاگردان دوره / Course Students"
        )

        notebook.add(
            self.enrollments_tab,
            text="ثبت نام / Enrollments"
        )

        notebook.add(
            self.details_tab,
            text="جزئیات دوره / Course Details"
        )

        notebook.bind(
            "<<NotebookTabChanged>>",
            self._on_tab_changed
        )

        self._notebook = notebook

    def _build_header(self):

        header = ttk.Frame(self)
        header.pack(fill="x")

        ttk.Button(
            header,
            text="< بازگشت / Back",
            command=self.on_back
        ).pack(side="left")

        ttk.Label(
            header,
            text="دوره‌های زمستانی / Winter Courses",
            font=("Segoe UI", 16, "bold")
        ).pack(
            side="left",
            padx=15
        )

        ttk.Label(
            header,
            text="(جدا از اطلاعات مکتب / Separate from school data)",
            font=("Segoe UI", 9, "italic"),
            foreground="#888888"
        ).pack(
            side="left",
            padx=10
        )

    def _on_any_change(self):

        self.courses_tab.refresh_teacher_dropdown()
        self.enrollments_tab.refresh_dropdowns()
        self.details_tab.refresh_course_dropdown()

    def _on_tab_changed(self, event):

        selected = self._notebook.select()

        if self._notebook.index(selected) == 4:
            self.details_tab.refresh_course_dropdown()


# ==========================================================================
# Course Teachers
# ==========================================================================

class CourseTeachersTab(ttk.Frame):

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

    def _build_form(self):

        form = ttk.LabelFrame(
            self,
            text="افزودن / ویرایش استاد دوره - Add / Edit Course Teacher",
            padding=15
        )

        form.pack(
            fill="x",
            pady=(0, 10)
        )

        self.name_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.notes_var = tk.StringVar()

        ttk.Label(
            form,
            text="نام / Name:"
        ).grid(
            row=0,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.name_var,
            width=25
        ).grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="تلفن / Phone:"
        ).grid(
            row=0,
            column=2,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.phone_var,
            width=25
        ).grid(
            row=0,
            column=3,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="یادداشت / Notes:"
        ).grid(
            row=1,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.notes_var,
            width=25
        ).grid(
            row=1,
            column=1,
            padx=5,
            pady=5
        )

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
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="پاک کردن / Clear",
            command=self._clear_form
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="حذف / Delete",
            command=self._handle_delete
        ).pack(side="left", padx=5)

    def _build_list(self):

        list_frame = ttk.Frame(self)

        list_frame.pack(
            fill="both",
            expand=True
        )

        columns = (
            "id",
            "name",
            "phone",
            "notes"
        )

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=10
        )

        headings = {
            "id": "ID",
            "name": "نام / Name",
            "phone": "تلفن / Phone",
            "notes": "یادداشت / Notes"
        }

        widths = {
            "id": 50,
            "name": 200,
            "phone": 130,
            "notes": 250
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

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self._handle_row_select
        )

    def refresh_list(self):

        for row in self.tree.get_children():
            self.tree.delete(row)

        for t in course_service.get_all_course_teachers(self.db):

            self.tree.insert(
                "",
                "end",
                values=(
                    t["id"],
                    t["full_name"],
                    t["phone"] or "",
                    t["notes"] or ""
                )
            )

    def _handle_row_select(self, event):

        selection = self.tree.selection()

        if not selection:
            return

        item = self.tree.item(selection[0])
        teacher_id = item["values"][0]

        t = course_service.get_course_teacher_by_id(
            self.db,
            teacher_id
        )

        if t is None:
            return

        self.selected_id = t["id"]

        self.name_var.set(
            t["full_name"] or ""
        )

        self.phone_var.set(
            t["phone"] or ""
        )

        self.notes_var.set(
            t["notes"] or ""
        )

    def _clear_form(self):

        self.selected_id = None

        self.name_var.set("")
        self.phone_var.set("")
        self.notes_var.set("")

        self.tree.selection_remove(
            self.tree.selection()
        )

    def _handle_save(self):

        try:

            if self.selected_id is None:

                course_service.add_course_teacher(
                    self.db,
                    self.name_var.get(),
                    self.phone_var.get(),
                    self.notes_var.get()
                )

                messagebox.showinfo(
                    "Saved",
                    "Course teacher added."
                )

            else:

                course_service.update_course_teacher(
                    self.db,
                    self.selected_id,
                    self.name_var.get(),
                    self.phone_var.get(),
                    self.notes_var.get()
                )

                messagebox.showinfo(
                    "Saved",
                    "Course teacher updated."
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
                f"Could not save:\n{e}"
            )

            return

        self._clear_form()
        self.refresh_list()
        self.on_change()

    def _handle_delete(self):

        if self.selected_id is None:

            messagebox.showwarning(
                "No Selection",
                "Select a teacher first."
            )

            return

        if not messagebox.askyesno(
            "Confirm Delete",
            "Delete this course teacher?"
        ):
            return

        try:

            course_service.delete_course_teacher(
                self.db,
                self.selected_id
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
                f"Could not delete:\n{e}"
            )

            return

        messagebox.showinfo(
            "Deleted",
            "Course teacher deleted."
        )

        self._clear_form()
        self.refresh_list()
        self.on_change()


# ==========================================================================
# Courses
# ==========================================================================

class CoursesTab(ttk.Frame):

    def __init__(self, parent, db, on_change):

        super().__init__(
            parent,
            padding=10
        )

        self.db = db
        self.on_change = on_change
        self.selected_id = None
        self.teacher_options = []

        self._build_form()
        self._build_list()
        self.refresh_teacher_dropdown()
        self.refresh_list()

    def _build_form(self):

        form = ttk.LabelFrame(
            self,
            text="افزودن / ویرایش دوره - Add / Edit Course",
            padding=15
        )

        form.pack(
            fill="x",
            pady=(0, 10)
        )

        self.name_var = tk.StringVar()
        self.teacher_var = tk.StringVar()
        self.percentage_var = tk.StringVar(value="50")
        self.start_var = tk.StringVar(
            value=date.today().strftime("%Y-%m-%d")
        )
        self.end_var = tk.StringVar()
        self.notes_var = tk.StringVar()

        ttk.Label(
            form,
            text="نام دوره / Course Name:"
        ).grid(
            row=0,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.name_var,
            width=25
        ).grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="استاد / Teacher:"
        ).grid(
            row=0,
            column=2,
            sticky="e",
            padx=5,
            pady=5
        )

        self.teacher_combo = ttk.Combobox(
            form,
            textvariable=self.teacher_var,
            values=[],
            state="readonly",
            width=23
        )

        self.teacher_combo.grid(
            row=0,
            column=3,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="سهم استاد ٪ / Teacher %:"
        ).grid(
            row=1,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.percentage_var,
            width=25
        ).grid(
            row=1,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="تاریخ شروع / Start Date:"
        ).grid(
            row=1,
            column=2,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.start_var,
            width=25
        ).grid(
            row=1,
            column=3,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="تاریخ ختم / End Date:"
        ).grid(
            row=2,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.end_var,
            width=25
        ).grid(
            row=2,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="یادداشت / Notes:"
        ).grid(
            row=2,
            column=2,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.notes_var,
            width=25
        ).grid(
            row=2,
            column=3,
            padx=5,
            pady=5
        )

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
            text="پاک کردن / Clear",
            command=self._clear_form
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="حذف / Delete",
            command=self._handle_delete
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="تازه‌سازی / Refresh",
            command=self._handle_refresh
        ).pack(side="left", padx=5)

    def _build_list(self):

        list_frame = ttk.Frame(self)

        list_frame.pack(
            fill="both",
            expand=True
        )

        columns = (
            "id",
            "name",
            "teacher",
            "percentage",
            "start",
            "end",
            "enrolled"
        )

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=10
        )

        headings = {
            "id": "ID",
            "name": "دوره / Course",
            "teacher": "استاد / Teacher",
            "percentage": "سهم ٪ / %",
            "start": "شروع / Start",
            "end": "ختم / End",
            "enrolled": "شاگردان / Enrolled"
        }

        widths = {
            "id": 40,
            "name": 150,
            "teacher": 140,
            "percentage": 60,
            "start": 100,
            "end": 100,
            "enrolled": 90
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

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self._handle_row_select
        )

    def refresh_teacher_dropdown(self):

        self.teacher_options = course_service.get_course_teacher_options(
            self.db
        )

        labels = [
            label
            for (_id, label)
            in self.teacher_options
        ]

        self.teacher_combo["values"] = labels

        if not labels:
            self.teacher_combo.set("")

    def _teacher_id_from_label(self, label):

        for tid, opt_label in self.teacher_options:

            if opt_label == label:
                return tid

        return None

    def _teacher_label_from_id(self, tid):

        for opt_id, label in self.teacher_options:

            if opt_id == tid:
                return label

        return ""

    def refresh_list(self):

        for row in self.tree.get_children():
            self.tree.delete(row)

        for c in course_service.get_all_courses(self.db):

            self.tree.insert(
                "",
                "end",
                values=(
                    c["id"],
                    c["name"],
                    c["teacher_name"] or "-",
                    f"{c['teacher_percentage']:.0f}%",
                    c["start_date"] or "",
                    c["end_date"] or "",
                    c["enrolled_count"]
                )
            )

    def _handle_refresh(self):

        self.refresh_teacher_dropdown()
        self._clear_form()
        self.refresh_list()

    def _handle_row_select(self, event):

        selection = self.tree.selection()

        if not selection:
            return

        item = self.tree.item(selection[0])
        course_id = item["values"][0]

        c = course_service.get_course_by_id(
            self.db,
            course_id
        )

        if c is None:
            return

        self.selected_id = c["id"]

        self.name_var.set(
            c["name"] or ""
        )

        self.teacher_var.set(
            self._teacher_label_from_id(
                c["teacher_id"]
            )
        )

        self.percentage_var.set(
            str(c["teacher_percentage"])
        )

        self.start_var.set(
            c["start_date"] or ""
        )

        self.end_var.set(
            c["end_date"] or ""
        )

        self.notes_var.set(
            c["notes"] or ""
        )

    def _clear_form(self):

        self.selected_id = None

        self.name_var.set("")
        self.teacher_var.set("")
        self.percentage_var.set("50")
        self.start_var.set(
            date.today().strftime("%Y-%m-%d")
        )
        self.end_var.set("")
        self.notes_var.set("")

        self.tree.selection_remove(
            self.tree.selection()
        )

    def _handle_save(self):

        teacher_id = self._teacher_id_from_label(
            self.teacher_var.get()
        )

        try:

            if self.selected_id is None:

                course_service.add_course(
                    self.db,
                    self.name_var.get(),
                    teacher_id,
                    self.percentage_var.get(),
                    self.start_var.get(),
                    self.end_var.get(),
                    self.notes_var.get()
                )

                messagebox.showinfo(
                    "Saved",
                    "Course added."
                )

            else:

                course_service.update_course(
                    self.db,
                    self.selected_id,
                    self.name_var.get(),
                    teacher_id,
                    self.percentage_var.get(),
                    self.start_var.get(),
                    self.end_var.get(),
                    self.notes_var.get()
                )

                messagebox.showinfo(
                    "Saved",
                    "Course updated."
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
                f"Could not save:\n{e}"
            )

            return

        self._clear_form()
        self.refresh_list()
        self.on_change()

    def _handle_delete(self):

        if self.selected_id is None:

            messagebox.showwarning(
                "No Selection",
                "Select a course first."
            )

            return

        if not messagebox.askyesno(
            "Confirm Delete",
            "Delete this course?"
        ):
            return

        try:

            course_service.delete_course(
                self.db,
                self.selected_id
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
                f"Could not delete:\n{e}"
            )

            return

        messagebox.showinfo(
            "Deleted",
            "Course deleted."
        )

        self._clear_form()
        self.refresh_list()
        self.on_change()


# ==========================================================================
# Course Students
# ==========================================================================

class CourseStudentsTab(ttk.Frame):

    def __init__(self, parent, db, on_change):

        super().__init__(
            parent,
            padding=10
        )

        self.db = db
        self.on_change = on_change
        self.selected_id = None

        self._build_form()
        self._build_search_and_list()
        self.refresh_list()

    def _build_form(self):

        form = ttk.LabelFrame(
            self,
            text="افزودن / ویرایش شاگرد دوره - Add / Edit Course Student",
            padding=15
        )

        form.pack(
            fill="x",
            pady=(0, 10)
        )

        self.name_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.notes_var = tk.StringVar()

        ttk.Label(
            form,
            text="نام / Name:"
        ).grid(
            row=0,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.name_var,
            width=25
        ).grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="تلفن / Phone:"
        ).grid(
            row=0,
            column=2,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.phone_var,
            width=25
        ).grid(
            row=0,
            column=3,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="یادداشت / Notes:"
        ).grid(
            row=1,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.notes_var,
            width=25
        ).grid(
            row=1,
            column=1,
            padx=5,
            pady=5
        )

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
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="پاک کردن / Clear",
            command=self._clear_form
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="حذف / Delete",
            command=self._handle_delete
        ).pack(side="left", padx=5)

    def _build_search_and_list(self):

        search_frame = ttk.Frame(self)

        search_frame.pack(
            fill="x",
            pady=(5, 5)
        )

        ttk.Label(
            search_frame,
            text="جستجو / Search:"
        ).pack(
            side="left",
            padx=(0, 5)
        )

        self.search_var = tk.StringVar()

        entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=30
        )

        entry.pack(
            side="left",
            padx=5
        )

        entry.bind(
            "<Return>",
            lambda e: self.refresh_list()
        )

        ttk.Button(
            search_frame,
            text="جستجو / Search",
            command=self.refresh_list
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            search_frame,
            text="تازه‌سازی / Refresh",
            command=self._handle_refresh
        ).pack(
            side="left",
            padx=5
        )

        # List container
        list_frame = ttk.Frame(self)

        list_frame.pack(
            fill="both",
            expand=True
        )

        columns = (
            "id",
            "name",
            "phone",
            "notes"
        )

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=9
        )

        headings = {
            "id": "ID",
            "name": "نام / Name",
            "phone": "تلفن / Phone",
            "notes": "یادداشت / Notes"
        }

        widths = {
            "id": 50,
            "name": 200,
            "phone": 130,
            "notes": 250
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

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self._handle_row_select
        )

    def refresh_list(self):

        for row in self.tree.get_children():
            self.tree.delete(row)

        search_text = self.search_var.get().strip()

        for s in course_service.get_all_course_students(
            self.db,
            search_text
        ):

            self.tree.insert(
                "",
                "end",
                values=(
                    s["id"],
                    s["full_name"],
                    s["phone"] or "",
                    s["notes"] or ""
                )
            )

    def _handle_refresh(self):

        self.search_var.set("")
        self._clear_form()
        self.refresh_list()

    def _handle_row_select(self, event):

        selection = self.tree.selection()

        if not selection:
            return

        item = self.tree.item(selection[0])
        student_id = item["values"][0]

        s = course_service.get_course_student_by_id(
            self.db,
            student_id
        )

        if s is None:
            return

        self.selected_id = s["id"]

        self.name_var.set(
            s["full_name"] or ""
        )

        self.phone_var.set(
            s["phone"] or ""
        )

        self.notes_var.set(
            s["notes"] or ""
        )

    def _clear_form(self):

        self.selected_id = None

        self.name_var.set("")
        self.phone_var.set("")
        self.notes_var.set("")

        self.tree.selection_remove(
            self.tree.selection()
        )

    def _handle_save(self):

        try:

            if self.selected_id is None:

                course_service.add_course_student(
                    self.db,
                    self.name_var.get(),
                    self.phone_var.get(),
                    self.notes_var.get()
                )

                messagebox.showinfo(
                    "Saved",
                    "Course student added."
                )

            else:

                course_service.update_course_student(
                    self.db,
                    self.selected_id,
                    self.name_var.get(),
                    self.phone_var.get(),
                    self.notes_var.get()
                )

                messagebox.showinfo(
                    "Saved",
                    "Course student updated."
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
                f"Could not save:\n{e}"
            )

            return

        self._clear_form()
        self.refresh_list()
        self.on_change()

    def _handle_delete(self):

        if self.selected_id is None:

            messagebox.showwarning(
                "No Selection",
                "Select a student first."
            )

            return

        if not messagebox.askyesno(
            "Confirm Delete",
            "Delete this course student?"
        ):
            return

        try:

            course_service.delete_course_student(
                self.db,
                self.selected_id
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
                f"Could not delete:\n{e}"
            )

            return

        messagebox.showinfo(
            "Deleted",
            "Course student deleted."
        )

        self._clear_form()
        self.refresh_list()
        self.on_change()


# ==========================================================================
# Enrollments
# ==========================================================================

class EnrollmentsTab(ttk.Frame):

    def __init__(self, parent, db, on_change):

        super().__init__(
            parent,
            padding=10
        )

        self.db = db
        self.on_change = on_change
        self.selected_id = None
        self.course_options = []
        self.student_options = []

        self._build_form()
        self._build_list()
        self.refresh_dropdowns()
        self.refresh_list()

    def _build_form(self):

        form = ttk.LabelFrame(
            self,
            text="ثبت نام شاگرد در دوره - Enroll Student in Course",
            padding=15
        )

        form.pack(
            fill="x",
            pady=(0, 10)
        )

        self.course_var = tk.StringVar()
        self.student_var = tk.StringVar()
        self.fee_var = tk.StringVar()
        self.date_var = tk.StringVar(
            value=date.today().strftime("%Y-%m-%d")
        )

        ttk.Label(
            form,
            text="دوره / Course:"
        ).grid(
            row=0,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        self.course_combo = ttk.Combobox(
            form,
            textvariable=self.course_var,
            values=[],
            state="readonly",
            width=25
        )

        self.course_combo.grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="شاگرد / Student:"
        ).grid(
            row=0,
            column=2,
            sticky="e",
            padx=5,
            pady=5
        )

        self.student_combo = ttk.Combobox(
            form,
            textvariable=self.student_var,
            values=[],
            state="readonly",
            width=25
        )

        self.student_combo.grid(
            row=0,
            column=3,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="فیس این شاگرد / This Student's Fee:"
        ).grid(
            row=1,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.fee_var,
            width=25
        ).grid(
            row=1,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="تاریخ ثبت نام / Enrollment Date:"
        ).grid(
            row=1,
            column=2,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.date_var,
            width=25
        ).grid(
            row=1,
            column=3,
            padx=5,
            pady=5
        )

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
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="پاک کردن / Clear",
            command=self._clear_form
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="حذف / Delete",
            command=self._handle_delete
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="تازه‌سازی / Refresh",
            command=self._handle_refresh
        ).pack(side="left", padx=5)

        ttk.Label(
            form,
            text=(
                "نوت: برای ثبت پرداخت شاگرد و مشاهده سهم استاد، "
                "به تب «جزئیات دوره» بروید.\n"
                "Note: to record student payments and see the teacher's "
                "share, go to the 'Course Details' tab."
            ),
            font=("Segoe UI", 8, "italic"),
            foreground="#888888"
        ).grid(
            row=3,
            column=0,
            columnspan=4,
            sticky="w",
            pady=(10, 0)
        )

    def _build_list(self):

        list_frame = ttk.Frame(self)

        list_frame.pack(
            fill="both",
            expand=True
        )

        columns = (
            "id",
            "course",
            "student",
            "phone",
            "fee",
            "date"
        )

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=10
        )

        headings = {
            "id": "ID",
            "course": "دوره / Course",
            "student": "شاگرد / Student",
            "phone": "تلفن / Phone",
            "fee": "فیس / Fee",
            "date": "تاریخ / Date"
        }

        widths = {
            "id": 50,
            "course": 150,
            "student": 160,
            "phone": 110,
            "fee": 100,
            "date": 110
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

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self._handle_row_select
        )

    def refresh_dropdowns(self):

        self.course_options = course_service.get_course_options(
            self.db
        )

        course_labels = [
            label
            for (_id, label)
            in self.course_options
        ]

        self.course_combo["values"] = course_labels

        if not course_labels:
            self.course_combo.set("")

        self.student_options = course_service.get_course_student_options(
            self.db
        )

        student_labels = [
            label
            for (_id, label)
            in self.student_options
        ]

        self.student_combo["values"] = student_labels

        if not student_labels:
            self.student_combo.set("")

    def _course_id_from_label(self, label):

        for cid, opt_label in self.course_options:

            if opt_label == label:
                return cid

        return None

    def _course_label_from_id(self, cid):

        for opt_id, label in self.course_options:

            if opt_id == cid:
                return label

        return ""

    def _student_id_from_label(self, label):

        for sid, opt_label in self.student_options:

            if opt_label == label:
                return sid

        return None

    def _student_label_from_id(self, sid):

        for opt_id, label in self.student_options:

            if opt_id == sid:
                return label

        return ""

    def refresh_list(self):

        for row in self.tree.get_children():
            self.tree.delete(row)

        for e in course_service.get_all_enrollments(self.db):

            self.tree.insert(
                "",
                "end",
                values=(
                    e["id"],
                    e["course_name"],
                    e["student_name"],
                    e["student_phone"] or "",
                    f"{e['fee_amount']:,.0f}",
                    e["enrollment_date"] or ""
                )
            )

    def _handle_refresh(self):

        self.refresh_dropdowns()
        self._clear_form()
        self.refresh_list()

    def _handle_row_select(self, event):

        selection = self.tree.selection()

        if not selection:
            return

        item = self.tree.item(selection[0])
        enrollment_id = item["values"][0]

        e = course_service.get_enrollment_by_id(
            self.db,
            enrollment_id
        )

        if e is None:
            return

        self.selected_id = e["id"]

        self.course_var.set(
            self._course_label_from_id(
                e["course_id"]
            )
        )

        self.student_var.set(
            self._student_label_from_id(
                e["course_student_id"]
            )
        )

        self.fee_var.set(
            str(e["fee_amount"])
        )

        self.date_var.set(
            e["enrollment_date"] or ""
        )

    def _clear_form(self):

        self.selected_id = None

        self.course_var.set("")
        self.student_var.set("")
        self.fee_var.set("")

        self.date_var.set(
            date.today().strftime("%Y-%m-%d")
        )

        self.tree.selection_remove(
            self.tree.selection()
        )

    def _handle_save(self):

        course_id = self._course_id_from_label(
            self.course_var.get()
        )

        student_id = self._student_id_from_label(
            self.student_var.get()
        )

        try:

            if self.selected_id is None:

                course_service.add_enrollment(
                    self.db,
                    course_id,
                    student_id,
                    self.fee_var.get(),
                    self.date_var.get()
                )

                messagebox.showinfo(
                    "Saved",
                    "Student enrolled."
                )

            else:

                course_service.update_enrollment(
                    self.db,
                    self.selected_id,
                    course_id,
                    student_id,
                    self.fee_var.get(),
                    self.date_var.get()
                )

                messagebox.showinfo(
                    "Saved",
                    "Enrollment updated."
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
                f"Could not save:\n{e}"
            )

            return

        self._clear_form()
        self.refresh_list()
        self.on_change()

    def _handle_delete(self):

        if self.selected_id is None:

            messagebox.showwarning(
                "No Selection",
                "Select an enrollment first."
            )

            return

        if not messagebox.askyesno(
            "Confirm Delete",
            "Remove this enrollment?"
        ):
            return

        try:

            course_service.delete_enrollment(
                self.db,
                self.selected_id
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
                f"Could not delete:\n{e}"
            )

            return

        messagebox.showinfo(
            "Deleted",
            "Enrollment removed."
        )

        self._clear_form()
        self.refresh_list()
        self.on_change()


# ==========================================================================
# Course Details
# ==========================================================================

class CourseDetailsTab(ttk.Frame):

    def __init__(self, parent, db, current_user):

        super().__init__(parent)

        self.db = db
        self.current_user = current_user

        self.course_options = []
        self.current_course_id = None

        self.selected_enrollment_id = None
        self.selected_payment_id = None
        self.selected_payout_id = None

        scrollable = ScrollableFrame(self)

        scrollable.pack(
            fill="both",
            expand=True
        )

        self.body = scrollable.interior

        self._build_course_selector()
        self._build_summary()
        self._build_enrollments_list()
        self._build_student_payment_form()
        self._build_teacher_payout_section()

        self.refresh_course_dropdown()

    def _build_course_selector(self):

        sel_frame = ttk.LabelFrame(
            self.body,
            text="انتخاب دوره / Select Course",
            padding=10
        )

        sel_frame.pack(
            fill="x",
            padx=10,
            pady=(10, 10)
        )

        self.course_var = tk.StringVar()

        self.course_combo = ttk.Combobox(
            sel_frame,
            textvariable=self.course_var,
            values=[],
            state="readonly",
            width=35
        )

        self.course_combo.pack(
            side="left",
            padx=5
        )

        ttk.Button(
            sel_frame,
            text="بارگذاری / Load",
            command=self._handle_load_course
        ).pack(
            side="left",
            padx=10
        )

    def refresh_course_dropdown(self):

        self.course_options = course_service.get_course_options(
            self.db
        )

        labels = [
            label
            for (_id, label)
            in self.course_options
        ]

        self.course_combo["values"] = labels

        if not labels:

            self.course_combo.set("")

            return

        if self.current_course_id is not None:

            self._load_course(
                self.current_course_id
            )

    def _course_id_from_label(self, label):

        for cid, opt_label in self.course_options:

            if opt_label == label:
                return cid

        return None

    def _handle_load_course(self):

        course_id = self._course_id_from_label(
            self.course_var.get()
        )

        if course_id is None:

            messagebox.showwarning(
                "No Selection",
                "Select a course first."
            )

            return

        self._load_course(course_id)

    def _load_course(self, course_id):

        self.current_course_id = course_id
        self.selected_enrollment_id = None
        self.selected_payment_id = None
        self.selected_payout_id = None

        try:

            summary = course_payment_service.get_course_financial_summary(
                self.db,
                course_id
            )

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"Could not load course:\n{e}"
            )

            return

        self._render_summary(summary)
        self._refresh_enrollments_list()
        self._refresh_payouts_list()

    def _build_summary(self):

        self.summary_frame = ttk.LabelFrame(
            self.body,
            text="خلص مالی دوره / Course Financial Summary",
            padding=10
        )

        self.summary_frame.pack(
            fill="x",
            padx=10,
            pady=(0, 10)
        )

        self.summary_label = ttk.Label(
            self.summary_frame,
            text=(
                "یک دوره را انتخاب و «بارگذاری» را کلیک کنید.\n"
                "Select a course and click Load."
            ),
            font=("Segoe UI", 10),
            foreground="#666666",
            justify="left"
        )

        self.summary_label.pack(
            anchor="w"
        )

    def _render_summary(self, summary):

        course = summary["course"]

        remaining_color = (
            "#166534"
            if summary["teacher_remaining"] <= 0
            else "#b91c1c"
        )

        text = (
            f"دوره / Course: {course['name']}   "
            f"(سهم استاد / Teacher %: "
            f"{course['teacher_percentage']:.0f}%)\n\n"

            f"مجموع دریافت شده از شاگردان / "
            f"Total Collected from Students: "
            f"{summary['total_collected']:,.0f}\n"

            f"سهم مکتب / School's Share: "
            f"{summary['school_share']:,.0f}\n\n"

            f"سهم استاد (محاسبه شده) / "
            f"Teacher's Share (calculated): "
            f"{summary['teacher_owed']:,.0f}\n"

            f"پرداخت شده به استاد / "
            f"Already Paid to Teacher: "
            f"{summary['teacher_paid']:,.0f}\n"
        )

        self.summary_label.config(
            text=text,
            foreground="black"
        )

        if hasattr(
            self,
            "_remaining_label"
        ):

            self._remaining_label.destroy()

        self._remaining_label = ttk.Label(
            self.summary_frame,
            text=(
                f"باقی مانده به استاد / "
                f"Still Owed to Teacher: "
                f"{summary['teacher_remaining']:,.0f}"
            ),
            font=("Segoe UI", 10, "bold"),
            foreground=remaining_color
        )

        self._remaining_label.pack(
            anchor="w",
            pady=(5, 0)
        )

    def _build_enrollments_list(self):

        ttk.Label(
            self.body,
            text=(
                "شاگردان این دوره / "
                "Students in This Course"
            ),
            font=("Segoe UI", 10, "bold")
        ).pack(
            anchor="w",
            padx=10,
            pady=(5, 5)
        )

        list_frame = ttk.Frame(self.body)

        list_frame.pack(
            fill="x",
            padx=10
        )

        columns = (
            "student",
            "fee",
            "paid",
            "remaining"
        )

        self.enroll_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=6
        )

        headings = {
            "student": "شاگرد / Student",
            "fee": "فیس / Fee",
            "paid": "پرداخت شده / Paid",
            "remaining": "باقی مانده / Remaining"
        }

        widths = {
            "student": 200,
            "fee": 100,
            "paid": 100,
            "remaining": 100
        }

        for col in columns:

            self.enroll_tree.heading(
                col,
                text=headings[col]
            )

            self.enroll_tree.column(
                col,
                width=widths[col],
                anchor="center"
            )

        self.enroll_tree.pack(
            side="left",
            fill="x",
            expand=True
        )

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.enroll_tree.yview
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.enroll_tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.enroll_tree.bind(
            "<<TreeviewSelect>>",
            self._handle_enrollment_select
        )

    def _refresh_enrollments_list(self):

        for row in self.enroll_tree.get_children():
            self.enroll_tree.delete(row)

        if self.current_course_id is None:
            return

        enrollments = course_service.get_all_enrollments(
            self.db,
            self.current_course_id
        )

        for e in enrollments:

            summary = course_payment_service.get_enrollment_summary(
                self.db,
                e["id"]
            )

            self.enroll_tree.insert(
                "",
                "end",
                iid=str(e["id"]),
                values=(
                    e["student_name"],
                    f"{summary['total_fee']:,.0f}",
                    f"{summary['total_paid']:,.0f}",
                    f"{summary['remaining']:,.0f}"
                )
            )

    def _handle_enrollment_select(self, event):

        selection = self.enroll_tree.selection()

        if not selection:

            self.selected_enrollment_id = None

            return

        self.selected_enrollment_id = int(
            selection[0]
        )

        self._refresh_payments_list()

    def _build_student_payment_form(self):

        form = ttk.LabelFrame(
            self.body,
            text=(
                "ثبت پرداخت شاگرد "
                "(شاگرد انتخاب شده بالا) / "
                "Record Student Payment "
                "(selected above)"
            ),
            padding=10
        )

        form.pack(
            fill="x",
            padx=10,
            pady=(10, 10)
        )

        self.pay_amount_var = tk.StringVar()
        self.pay_date_var = tk.StringVar(
            value=date.today().strftime("%Y-%m-%d")
        )
        self.pay_note_var = tk.StringVar()
        self.pay_overpay_var = tk.BooleanVar(
            value=False
        )

        ttk.Label(
            form,
            text="مبلغ / Amount:"
        ).grid(
            row=0,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.pay_amount_var,
            width=18
        ).grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="تاریخ / Date:"
        ).grid(
            row=0,
            column=2,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.pay_date_var,
            width=18
        ).grid(
            row=0,
            column=3,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="یادداشت / Note:"
        ).grid(
            row=0,
            column=4,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.pay_note_var,
            width=18
        ).grid(
            row=0,
            column=5,
            padx=5,
            pady=5
        )

        ttk.Checkbutton(
            form,
            text="اجازه پرداخت اضافی / Allow overpayment",
            variable=self.pay_overpay_var
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            padx=5,
            pady=(5, 0)
        )

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=2, column=0, columnspan=6, pady=(10, 0))
        ttk.Button(btn_frame, text="ثبت پرداخت / Save Payment", command=self._handle_save_payment).pack(side="left",
                                                                                                        padx=5)
        ttk.Button(btn_frame, text="حذف پرداخت انتخاب شده / Delete Selected Payment",
                   command=self._handle_delete_payment).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="چاپ رسید / Print Receipt", command=self._handle_print_course_receipt).pack(
            side="left", padx=5)

        ttk.Label(
            self.body,
            text=(
                "تاریخچه پرداخت شاگرد / "
                "Student Payment History"
            ),
            font=("Segoe UI", 9, "bold")
        ).pack(
            anchor="w",
            padx=10,
            pady=(5, 3)
        )

        list_frame = ttk.Frame(self.body)

        list_frame.pack(
            fill="x",
            padx=10
        )

        columns = (
            "id",
            "amount",
            "date",
            "note"
        )

        self.pay_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=4
        )

        headings = {
            "id": "ID",
            "amount": "مبلغ / Amount",
            "date": "تاریخ / Date",
            "note": "یادداشت / Note"
        }

        widths = {
            "id": 50,
            "amount": 110,
            "date": 110,
            "note": 250
        }

        for col in columns:

            self.pay_tree.heading(
                col,
                text=headings[col]
            )

            self.pay_tree.column(
                col,
                width=widths[col],
                anchor="center"
            )

        self.pay_tree.pack(
            side="left",
            fill="x",
            expand=True
        )

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.pay_tree.yview
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.pay_tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.pay_tree.bind(
            "<<TreeviewSelect>>",
            self._handle_payment_row_select
        )

    def _refresh_payments_list(self):

        for row in self.pay_tree.get_children():
            self.pay_tree.delete(row)

        if self.selected_enrollment_id is None:
            return

        for p in course_payment_service.get_payments_for_enrollment(
            self.db,
            self.selected_enrollment_id
        ):

            self.pay_tree.insert(
                "",
                "end",
                values=(
                    p["id"],
                    f"{p['amount']:,.0f}",
                    p["payment_date"],
                    p["note"] or ""
                )
            )

    def _handle_payment_row_select(self, event):

        selection = self.pay_tree.selection()

        if not selection:

            self.selected_payment_id = None

            return

        item = self.pay_tree.item(
            selection[0]
        )

        self.selected_payment_id = item["values"][0]

    def _handle_save_payment(self):

        if self.selected_enrollment_id is None:

            messagebox.showwarning(
                "No Selection",
                "Select a student from the list above first."
            )

            return

        try:

            course_payment_service.add_course_payment(
                self.db,
                self.selected_enrollment_id,
                self.pay_amount_var.get(),
                self.pay_date_var.get(),
                self.pay_note_var.get(),
                allow_overpayment=self.pay_overpay_var.get()
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
            "Payment recorded."
        )

        self.pay_amount_var.set("")
        self.pay_note_var.set("")
        self.pay_overpay_var.set(False)

        self._refresh_payments_list()
        self._refresh_enrollments_list()
        self._reload_summary()

    def _handle_delete_payment(self):

        if not check_owner_action(
            self.current_user,
            "حذف پرداخت شاگرد دوره / Deleting a course student payment"
        ):
            return

        if self.selected_payment_id is None:

            messagebox.showwarning(
                "No Selection",
                "Select a payment from the history list first."
            )

            return

        if not messagebox.askyesno(
            "Confirm Delete",
            "Delete this payment?"
        ):
            return

        try:

            course_payment_service.delete_course_payment(
                self.db,
                self.selected_payment_id
            )

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"Could not delete:\n{e}"
            )

            return

        messagebox.showinfo(
            "Deleted",
            "Payment deleted."
        )

        self.selected_payment_id = None

        self._refresh_payments_list()
        self._refresh_enrollments_list()
        self._reload_summary()
    def _handle_print_course_receipt(self):
        if self.selected_payment_id is None:
            messagebox.showwarning(
                "No Selection",
                "Select a payment from the history list first, then click Print Receipt."
            )
            return

        try:
            file_path = receipt_service.save_and_open_course_receipt(self.db, self.selected_payment_id)
        except ValueError as e:
            messagebox.showwarning("Cannot Generate Receipt", str(e))
            return
        except Exception as e:
            messagebox.showerror("Error", f"Could not generate receipt:\n{e}")
            return

        messagebox.showinfo(
            "Receipt Generated",
            f"Receipt opened in your browser.\n\nSaved at:\n{file_path}"
        )

    def _build_teacher_payout_section(self):

        form = ttk.LabelFrame(
            self.body,
            text="پرداخت به استاد / Pay Teacher",
            padding=10
        )

        form.pack(
            fill="x",
            padx=10,
            pady=(10, 10)
        )

        self.payout_amount_var = tk.StringVar()
        self.payout_date_var = tk.StringVar(
            value=date.today().strftime("%Y-%m-%d")
        )
        self.payout_note_var = tk.StringVar()
        self.payout_overpay_var = tk.BooleanVar(
            value=False
        )

        ttk.Label(
            form,
            text="مبلغ / Amount:"
        ).grid(
            row=0,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.payout_amount_var,
            width=18
        ).grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="تاریخ / Date:"
        ).grid(
            row=0,
            column=2,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.payout_date_var,
            width=18
        ).grid(
            row=0,
            column=3,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="یادداشت / Note:"
        ).grid(
            row=0,
            column=4,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.payout_note_var,
            width=18
        ).grid(
            row=0,
            column=5,
            padx=5,
            pady=5
        )

        ttk.Checkbutton(
            form,
            text="اجازه پرداخت اضافی / Allow overpayment",
            variable=self.payout_overpay_var
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            padx=5,
            pady=(5, 0)
        )

        btn_frame = ttk.Frame(form)

        btn_frame.grid(
            row=2,
            column=0,
            columnspan=6,
            pady=(10, 0)
        )

        ttk.Button(
            btn_frame,
            text="ثبت پرداخت به استاد / Record Payout",
            command=self._handle_save_payout
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            btn_frame,
            text="حذف پرداخت انتخاب شده / Delete Selected Payout",
            command=self._handle_delete_payout
        ).pack(
            side="left",
            padx=5
        )

        ttk.Label(
            self.body,
            text=(
                "تاریخچه پرداخت به استاد / "
                "Teacher Payout History"
            ),
            font=("Segoe UI", 9, "bold")
        ).pack(
            anchor="w",
            padx=10,
            pady=(10, 3)
        )

        list_frame = ttk.Frame(self.body)

        list_frame.pack(
            fill="x",
            padx=10,
            pady=(0, 15)
        )

        columns = (
            "id",
            "amount",
            "date",
            "note"
        )

        self.payout_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=4
        )

        headings = {
            "id": "ID",
            "amount": "مبلغ / Amount",
            "date": "تاریخ / Date",
            "note": "یادداشت / Note"
        }

        widths = {
            "id": 50,
            "amount": 110,
            "date": 110,
            "note": 250
        }

        for col in columns:

            self.payout_tree.heading(
                col,
                text=headings[col]
            )

            self.payout_tree.column(
                col,
                width=widths[col],
                anchor="center"
            )

        self.payout_tree.pack(
            side="left",
            fill="x",
            expand=True
        )

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.payout_tree.yview
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.payout_tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.payout_tree.bind(
            "<<TreeviewSelect>>",
            self._handle_payout_row_select
        )

    def _refresh_payouts_list(self):

        for row in self.payout_tree.get_children():
            self.payout_tree.delete(row)

        if self.current_course_id is None:
            return

        for p in course_payment_service.get_teacher_payouts(
            self.db,
            self.current_course_id
        ):

            self.payout_tree.insert(
                "",
                "end",
                values=(
                    p["id"],
                    f"{p['amount']:,.0f}",
                    p["payment_date"],
                    p["note"] or ""
                )
            )

    def _handle_payout_row_select(self, event):

        selection = self.payout_tree.selection()

        if not selection:

            self.selected_payout_id = None

            return

        item = self.payout_tree.item(
            selection[0]
        )

        self.selected_payout_id = item["values"][0]

    def _handle_save_payout(self):

        if self.current_course_id is None:

            messagebox.showwarning(
                "No Course Loaded",
                "Load a course first."
            )

            return

        try:

            course_payment_service.add_teacher_payout(
                self.db,
                self.current_course_id,
                self.payout_amount_var.get(),
                self.payout_date_var.get(),
                self.payout_note_var.get(),
                allow_overpayment=self.payout_overpay_var.get()
            )

        except ValueError as e:

            messagebox.showwarning(
                "Cannot Save Payout",
                str(e)
            )

            return

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"Could not save payout:\n{e}"
            )

            return

        messagebox.showinfo(
            "Saved",
            "Teacher payout recorded."
        )

        self.payout_amount_var.set("")
        self.payout_note_var.set("")
        self.payout_overpay_var.set(False)

        self._refresh_payouts_list()
        self._reload_summary()

    def _handle_delete_payout(self):

        if not check_owner_action(
            self.current_user,
            "حذف پرداخت استاد / Deleting a teacher payout"
        ):
            return

        if self.selected_payout_id is None:

            messagebox.showwarning(
                "No Selection",
                "Select a payout from the history list first."
            )

            return

        if not messagebox.askyesno(
            "Confirm Delete",
            "Delete this payout record?"
        ):
            return

        try:

            course_payment_service.delete_teacher_payout(
                self.db,
                self.selected_payout_id
            )

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"Could not delete:\n{e}"
            )

            return

        messagebox.showinfo(
            "Deleted",
            "Payout deleted."
        )

        self.selected_payout_id = None

        self._refresh_payouts_list()
        self._reload_summary()

    def _reload_summary(self):

        if self.current_course_id is None:
            return

        summary = course_payment_service.get_course_financial_summary(
            self.db,
            self.current_course_id
        )

        self._render_summary(summary)