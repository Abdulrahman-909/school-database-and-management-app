"""
ui/library.py

Library / Books module: Add / Edit / Delete / Search / Refresh, plus Issue / Return.
Increasing a book's total copies (adding new stock) is restricted to the school owner - managers can still decrease it (recording lost/damaged copies) and issue/return normally.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from services import library_service
from services.permissions import check_owner_action


class LibraryFrame(ttk.Frame):
    def __init__(self, parent, db, current_user, on_back):
        super().__init__(parent, padding=15)
        self.db = db
        self.current_user = current_user
        self.on_back = on_back

        self.selected_book_id = None

        self.pack(fill="both", expand=True)

        self._build_header()
        self._build_summary()
        self._build_form()
        self._build_search_and_list()

        self.refresh_list()

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _build_header(self):
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 10))

        ttk.Button(
            header,
            text="< بازگشت / Back",
            command=self.on_back
        ).pack(side="left")

        ttk.Label(
            header,
            text="کتابخانه / Library",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=15)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _build_summary(self):
        self.summary_label = ttk.Label(
            self,
            text="",
            font=("Segoe UI", 10, "bold")
        )
        self.summary_label.pack(anchor="w", pady=(0, 10))

    def _refresh_summary(self):
        total = library_service.get_total_books(self.db)
        available = library_service.get_total_available(self.db)
        issued = library_service.get_total_issued(self.db)

        self.summary_label.config(
            text=(
                f"مجموع کتاب‌ها / Total Copies: {total}    |    "
                f"موجود / Available: {available}    |    "
                f"توزیع شده / Issued: {issued}"
            )
        )

    # ------------------------------------------------------------------
    # Form
    # ------------------------------------------------------------------

    def _build_form(self):
        form = ttk.LabelFrame(
            self,
            text="افزودن / ویرایش کتاب - Add / Edit Book",
            padding=15
        )
        form.pack(fill="x", pady=(0, 10))

        self.title_var = tk.StringVar()
        self.author_var = tk.StringVar()
        self.total_copies_var = tk.StringVar(value="1")

        ttk.Label(
            form,
            text="نام کتاب / Title:"
        ).grid(row=0, column=0, sticky="e", padx=5, pady=5)

        ttk.Entry(
            form,
            textvariable=self.title_var,
            width=28
        ).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(
            form,
            text="نویسنده / Author:"
        ).grid(row=0, column=2, sticky="e", padx=5, pady=5)

        ttk.Entry(
            form,
            textvariable=self.author_var,
            width=28
        ).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(
            form,
            text="تعداد کل / Total Copies:"
        ).grid(row=1, column=0, sticky="e", padx=5, pady=5)

        ttk.Entry(
            form,
            textvariable=self.total_copies_var,
            width=28
        ).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(
            form,
            text=(
                "نوت: فقط مالک می‌تواند تعداد کل را افزایش دهد؛ مدیر می‌تواند کاهش دهد (کتاب گم/خراب شده).\n"
                "Note: only the owner can increase total copies; managers can decrease it (lost/damaged)."
            ),
            font=("Segoe UI", 8, "italic"),
            foreground="#888888"
        ).grid(
            row=2,
            column=0,
            columnspan=4,
            sticky="w",
            pady=(5, 0)
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
            text="پاک کردن فورم / Clear Form",
            command=self._clear_form
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="حذف / Delete",
            command=self._handle_delete
        ).pack(side="left", padx=5)

        ttk.Separator(
            btn_frame,
            orient="vertical"
        ).pack(side="left", fill="y", padx=10)

        ttk.Button(
            btn_frame,
            text="توزیع یک نسخه / Issue One Copy",
            command=self._handle_issue
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="برگشت یک نسخه / Return One Copy",
            command=self._handle_return
        ).pack(side="left", padx=5)

    # ------------------------------------------------------------------
    # Search + List
    # ------------------------------------------------------------------

    def _build_search_and_list(self):
        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", pady=(5, 5))

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
        search_entry.pack(side="left", padx=5)

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

        # --------------------------------------------------------------
        # LIST FRAME
        #
        # The scrollbar belongs ONLY to the book list.
        # It does NOT scroll the entire Library tab.
        # --------------------------------------------------------------

        list_frame = ttk.Frame(self)
        list_frame.pack(
            fill="both",
            expand=True,
            pady=(5, 0)
        )

        columns = (
            "id",
            "title",
            "author",
            "total",
            "available",
            "issued"
        )

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=13
        )

        headings = {
            "id": "ID",
            "title": "نام کتاب / Title",
            "author": "نویسنده / Author",
            "total": "تعداد کل / Total",
            "available": "موجود / Available",
            "issued": "توزیع شده / Issued",
        }

        widths = {
            "id": 50,
            "title": 220,
            "author": 150,
            "total": 90,
            "available": 100,
            "issued": 100
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
            "none_available",
            background="#f8d7da"
        )

        # --------------------------------------------------------------
        # Treeview + scrollbar
        # --------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def refresh_list(self):
        self._refresh_summary()

        for row in self.tree.get_children():
            self.tree.delete(row)

        search_text = self.search_var.get().strip()

        books = library_service.get_all_books(
            self.db,
            search_text
        )

        for b in books:
            issued = (
                b["total_copies"]
                - b["available_copies"]
            )

            tag = (
                "none_available"
                if b["available_copies"] <= 0
                else ""
            )

            self.tree.insert(
                "",
                "end",
                values=(
                    b["id"],
                    b["title"],
                    b["author"] or "",
                    b["total_copies"],
                    b["available_copies"],
                    issued
                ),
                tags=(tag,) if tag else ()
            )

    def _handle_refresh(self):
        self.search_var.set("")
        self._clear_form()
        self.refresh_list()

    # ------------------------------------------------------------------
    # Row selection
    # ------------------------------------------------------------------

    def _handle_row_select(self, event):
        selection = self.tree.selection()

        if not selection:
            return

        item = self.tree.item(selection[0])
        book_id = item["values"][0]

        book = library_service.get_book_by_id(
            self.db,
            book_id
        )

        if book is None:
            return

        self.selected_book_id = book["id"]

        self.title_var.set(
            book["title"] or ""
        )

        self.author_var.set(
            book["author"] or ""
        )

        self.total_copies_var.set(
            str(book["total_copies"])
        )

    def _clear_form(self):
        self.selected_book_id = None

        self.title_var.set("")
        self.author_var.set("")
        self.total_copies_var.set("1")

        self.tree.selection_remove(
            self.tree.selection()
        )

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def _handle_save(self):
        try:
            if self.selected_book_id is None:

                library_service.add_book(
                    self.db,
                    self.title_var.get(),
                    self.author_var.get(),
                    self.total_copies_var.get()
                )

                messagebox.showinfo(
                    "Saved",
                    "Book added successfully."
                )

            else:

                current_book = library_service.get_book_by_id(
                    self.db,
                    self.selected_book_id
                )

                try:
                    new_total = int(
                        self.total_copies_var.get()
                    )
                except (TypeError, ValueError):
                    new_total = None

                if (
                    current_book is not None
                    and new_total is not None
                    and new_total > current_book["total_copies"]
                ):
                    if not check_owner_action(
                        self.current_user,
                        "افزایش تعداد کل کتاب / Increasing a book's total copies"
                    ):
                        return

                library_service.update_book(
                    self.db,
                    self.selected_book_id,
                    self.title_var.get(),
                    self.author_var.get(),
                    self.total_copies_var.get()
                )

                messagebox.showinfo(
                    "Saved",
                    "Book updated successfully."
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
                f"Could not save book:\n{e}"
            )
            return

        self._clear_form()
        self.refresh_list()

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def _handle_delete(self):
        if self.selected_book_id is None:
            messagebox.showwarning(
                "No Selection",
                "Select a book from the list first."
            )
            return

        title = self.title_var.get()

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{title}'?\n"
            "This cannot be undone."
        )

        if not confirm:
            return

        try:
            library_service.delete_book(
                self.db,
                self.selected_book_id
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
                f"Could not delete book:\n{e}"
            )
            return

        messagebox.showinfo(
            "Deleted",
            "Book deleted."
        )

        self._clear_form()
        self.refresh_list()

    # ------------------------------------------------------------------
    # Issue
    # ------------------------------------------------------------------

    def _handle_issue(self):
        if self.selected_book_id is None:
            messagebox.showwarning(
                "No Selection",
                "Select a book from the list first."
            )
            return

        try:
            library_service.issue_copy(
                self.db,
                self.selected_book_id
            )

        except ValueError as e:
            messagebox.showwarning(
                "Cannot Issue",
                str(e)
            )
            return

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not issue book:\n{e}"
            )
            return

        self.refresh_list()

    # ------------------------------------------------------------------
    # Return
    # ------------------------------------------------------------------

    def _handle_return(self):
        if self.selected_book_id is None:
            messagebox.showwarning(
                "No Selection",
                "Select a book from the list first."
            )
            return

        try:
            library_service.return_copy(
                self.db,
                self.selected_book_id
            )

        except ValueError as e:
            messagebox.showwarning(
                "Cannot Return",
                str(e)
            )
            return

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not return book:\n{e}"
            )
            return

        self.refresh_list()