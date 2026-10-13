"""
ui/classes.py

Classes module: Add / Edit / Delete / Refresh.
Current student count and available seats are calculated live from
the students table, not stored or typed in.
All database access goes through services/class_service.py.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from services import class_service
from ui.scrollable import ScrollableFrame


class ClassesFrame(ttk.Frame):
    def __init__(self, parent, db, on_back):
        super().__init__(parent, padding=15)
        self.db = db
        self.on_back = on_back

        self.selected_class_id = None

        self.pack(fill="both", expand=True)

        scrollable = ScrollableFrame(self)
        scrollable.pack(fill="both", expand=True)
        self.body = scrollable.body

        self._build_header()
        self._build_form()
        self._build_list()

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
            text="صنوف / Classes",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=15)

    # ------------------------------------------------------------------
    # Form
    # ------------------------------------------------------------------

    def _build_form(self):
        form = ttk.LabelFrame(
            self.body,
            text="افزودن / ویرایش صنف - Add / Edit Class",
            padding=15
        )
        form.pack(fill="x", pady=(0, 10))

        self.name_var = tk.StringVar()
        self.section_var = tk.StringVar()
        self.capacity_var = tk.StringVar(value="30")

        ttk.Label(
            form,
            text="صنف / Name:"
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
            text="شعبه / Section:"
        ).grid(
            row=0,
            column=2,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.section_var,
            width=25
        ).grid(
            row=0,
            column=3,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="ظرفیت / Capacity:"
        ).grid(
            row=1,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.capacity_var,
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
            text="پاک کردن فورم / Clear Form",
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

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def _build_list(self):
        columns = (
            "id",
            "name",
            "section",
            "capacity",
            "current",
            "available"
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
            pady=(5, 0)
        )
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=15
        )

        headings = {
            "id": "ID",
            "name": "صنف / Name",
            "section": "شعبه / Section",
            "capacity": "ظرفیت / Capacity",
            "current": "شاگردان فعلی / Current",
            "available": "جای خالی / Available",
        }

        widths = {
            "id": 50,
            "name": 150,
            "section": 100,
            "capacity": 100,
            "current": 130,
            "available": 130
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

        self.tree.tag_configure(
            "full",
            background="#f8d7da"
        )

        self.tree.tag_configure(
            "near_full",
            background="#fff3cd"
        )

        # Treeview fills the list area
        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        # Scrollbar ONLY for the class list
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

        classes = class_service.get_all_classes(self.db)

        for c in classes:
            available = c["available_seats"]

            tag = ""

            if available <= 0:
                tag = "full"

            elif available <= 3:
                tag = "near_full"

            self.tree.insert(
                "",
                "end",
                values=(
                    c["id"],
                    c["name"],
                    c["section"] or "-",
                    c["capacity"],
                    c["current_students"],
                    available
                ),
                tags=(tag,) if tag else ()
            )

    def _handle_refresh(self):
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
        class_id = item["values"][0]

        class_row = class_service.get_class_by_id(
            self.db,
            class_id
        )

        if class_row is None:
            return

        self.selected_class_id = class_row["id"]

        self.name_var.set(
            class_row["name"] or ""
        )

        self.section_var.set(
            class_row["section"] or ""
        )

        self.capacity_var.set(
            str(class_row["capacity"])
        )

    def _clear_form(self):
        self.selected_class_id = None

        self.name_var.set("")
        self.section_var.set("")
        self.capacity_var.set("30")

        self.tree.selection_remove(
            self.tree.selection()
        )

    # ------------------------------------------------------------------
    # Save / Delete
    # ------------------------------------------------------------------

    def _handle_save(self):
        try:
            if self.selected_class_id is None:
                class_service.add_class(
                    self.db,
                    self.name_var.get(),
                    self.section_var.get(),
                    self.capacity_var.get(),
                )

                messagebox.showinfo(
                    "Saved",
                    "Class added successfully."
                )

            else:
                class_service.update_class(
                    self.db,
                    self.selected_class_id,
                    self.name_var.get(),
                    self.section_var.get(),
                    self.capacity_var.get(),
                )

                messagebox.showinfo(
                    "Saved",
                    "Class updated successfully."
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
                f"Could not save class:\n{e}"
            )
            return

        self._clear_form()
        self.refresh_list()

    def _handle_delete(self):
        if self.selected_class_id is None:
            messagebox.showwarning(
                "No Selection",
                "Select a class from the list first."
            )
            return

        name = self.name_var.get()

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{name}'?\n"
            "This cannot be undone."
        )

        if not confirm:
            return

        try:
            class_service.delete_class(
                self.db,
                self.selected_class_id
            )

        except ValueError as e:
            # e.g. "students are still assigned" - this is an expected,
            # helpful block, not a crash.
            messagebox.showwarning(
                "Cannot Delete",
                str(e)
            )
            return

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not delete class:\n{e}"
            )
            return

        messagebox.showinfo(
            "Deleted",
            "Class deleted."
        )

        self._clear_form()
        self.refresh_list()