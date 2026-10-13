"""
ui/fees.py

Fee Structure module: Add / Edit / Delete / Refresh.
The amount entered here is a MONTHLY fee - the annual total (shown
here for reference only, and used everywhere else in the app) is
always monthly x 12, calculated live.
Deleting a fee entry is restricted to the school owner.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from services import fee_structure_service
from services import class_service
from services.permissions import check_owner_action
from ui.scrollable import ScrollableFrame


class FeeStructureFrame(ttk.Frame):
    def __init__(self, parent, db, current_user, on_back):
        super().__init__(parent, padding=15)
        self.db = db
        self.current_user = current_user
        self.on_back = on_back

        self.selected_fee_id = None
        self.class_options = []

        self.pack(fill="both", expand=True)

        scrollable = ScrollableFrame(self)
        scrollable.pack(fill="both", expand=True)
        self.body = scrollable.body

        self._build_header()
        self._build_form()
        self._build_list()

        self.refresh_list()

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
            text="ساختار فیس / Fee Structure",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=15)

    def _build_form(self):
        form = ttk.LabelFrame(
            self.body,
            text="افزودن / ویرایش فیس - Add / Edit Fee",
            padding=15
        )
        form.pack(fill="x", pady=(0, 10))

        self.class_var = tk.StringVar()
        self.year_var = tk.StringVar()
        self.amount_var = tk.StringVar()

        ttk.Label(
            form,
            text="صنف / Class:"
        ).grid(
            row=0,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        self.class_combo = ttk.Combobox(
            form,
            textvariable=self.class_var,
            values=[],
            state="readonly",
            width=25
        )

        self.class_combo.grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="سال تعلیمی / Academic Year:"
        ).grid(
            row=0,
            column=2,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.year_var,
            width=25
        ).grid(
            row=0,
            column=3,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="فیس ماهانه / Monthly Fee:"
        ).grid(
            row=1,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        ttk.Entry(
            form,
            textvariable=self.amount_var,
            width=25
        ).grid(
            row=1,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Label(
            form,
            text="نوت: این مبلغ برای هر ماه است (حمل تا قوس، ۹ ماه). مبلغ سالانه به صورت خودکار = مبلغ ماهانه × ۹ محاسبه می‌شود.\n"
                 "Note: this amount is PER MONTH (Hamal-Qaws, 9 months). Annual total is calculated automatically as monthly x 9.",
            font=("Segoe UI", 8, "italic"), foreground="#888888"
        ).grid(row=2, column=0, columnspan=4, sticky="w", pady=(5, 0))

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

        ttk.Button(
            btn_frame,
            text="تازه‌سازی / Refresh",
            command=self._handle_refresh
        ).pack(side="left", padx=5)

    def _build_list(self):
        columns = (
            "id",
            "class",
            "year",
            "monthly",
            "annual"
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
            "class": "صنف / Class",
            "year": "سال تعلیمی / Year",
            "monthly": "فیس ماهانه / Monthly",
            "annual": "سالانه ۹ ماه / Annual (x9)",
        }

        widths = {
            "id": 50,
            "class": 180,
            "year": 130,
            "monthly": 130,
            "annual": 170
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

        # Scrollbar ONLY for the fee list
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

    def refresh_list(self):
        self._load_class_options()

        for row in self.tree.get_children():
            self.tree.delete(row)

        fees = fee_structure_service.get_all_fee_structures(
            self.db
        )

        for f in fees:
            class_display = f["class_name"]

            if f["class_section"]:
                class_display = (
                    f"{f['class_name']} - "
                    f"{f['class_section']}"
                )

            from services.payment_service import MONTHS_PER_YEAR
            annual = f["amount"] * MONTHS_PER_YEAR

            self.tree.insert(
                "",
                "end",
                values=(
                    f["id"],
                    class_display,
                    f["academic_year"],
                    f"{f['amount']:,.0f}",
                    f"{annual:,.0f}"
                )
            )

    def _handle_refresh(self):
        self._clear_form()
        self.refresh_list()

    def _load_class_options(self):
        self.class_options = class_service.get_class_options(
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

    def _handle_row_select(self, event):
        selection = self.tree.selection()

        if not selection:
            return

        item = self.tree.item(selection[0])
        fee_id = item["values"][0]

        fee = fee_structure_service.get_fee_structure_by_id(
            self.db,
            fee_id
        )

        if fee is None:
            return

        self.selected_fee_id = fee["id"]

        self.class_var.set(
            self._class_label_from_id(
                fee["class_id"]
            )
        )

        self.year_var.set(
            fee["academic_year"] or ""
        )

        self.amount_var.set(
            str(fee["amount"])
        )

    def _clear_form(self):
        self.selected_fee_id = None

        self.class_var.set("")
        self.year_var.set("")
        self.amount_var.set("")

        self.tree.selection_remove(
            self.tree.selection()
        )

    def _handle_save(self):
        class_id = self._class_id_from_label(
            self.class_var.get()
        )

        try:
            if self.selected_fee_id is None:
                fee_structure_service.add_fee_structure(
                    self.db,
                    class_id,
                    self.year_var.get(),
                    self.amount_var.get()
                )

                messagebox.showinfo(
                    "Saved",
                    "Monthly fee added successfully."
                )

            else:
                fee_structure_service.update_fee_structure(
                    self.db,
                    self.selected_fee_id,
                    class_id,
                    self.year_var.get(),
                    self.amount_var.get()
                )

                messagebox.showinfo(
                    "Saved",
                    "Monthly fee updated successfully."
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
                f"Could not save fee structure:\n{e}"
            )
            return

        self._clear_form()
        self.refresh_list()

    def _handle_delete(self):
        if not check_owner_action(
            self.current_user,
            "حذف رکورد فیس / Deleting a fee structure entry"
        ):
            return

        if self.selected_fee_id is None:
            messagebox.showwarning(
                "No Selection",
                "Select a fee entry from the list first."
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this fee entry?\n"
            "This cannot be undone."
        )

        if not confirm:
            return

        try:
            fee_structure_service.delete_fee_structure(
                self.db,
                self.selected_fee_id
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not delete fee entry:\n{e}"
            )
            return

        messagebox.showinfo(
            "Deleted",
            "Fee entry deleted."
        )

        self._clear_form()
        self.refresh_list()