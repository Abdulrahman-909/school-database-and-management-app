"""
ui/backup.py

Backup module: create timestamped backups, restore from a backup, and
delete old backup files. Restore and Delete are both restricted to the
school owner (see services/permissions.py) - anyone can still create a
new backup.
"""

import os
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from services.permissions import check_owner_action
from services import settings_service


class BackupFrame(ttk.Frame):
    def __init__(self, parent, db, current_user, on_back, on_restore_requested):
        super().__init__(parent, padding=20)
        self.db = db
        self.current_user = current_user
        self.on_back = on_back
        self.on_restore_requested = on_restore_requested

        self.backups_dir = self._get_backups_dir()

        self.pack(fill="both", expand=True)

        self._build_header()
        self._build_actions()
        self._build_list()

        self.refresh_list()

    def _get_backups_dir(self) -> Path:
        custom_folder = settings_service.get_backup_folder()
        if custom_folder:
            backups_dir = Path(custom_folder)
            backups_dir.mkdir(parents=True, exist_ok=True)
            return backups_dir

        project_root = Path(__file__).resolve().parent.parent
        backups_dir = project_root / "data" / "backups"
        backups_dir.mkdir(parents=True, exist_ok=True)
        return backups_dir

    def _build_header(self):
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 15))

        ttk.Button(
            header,
            text="< بازگشت / Back",
            command=self.on_back
        ).pack(side="left")

        ttk.Label(
            header,
            text="بکاپ / Backup",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=15)

    def _build_actions(self):
        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(0, 15))

        ttk.Button(
            actions,
            text="ایجاد بکاپ جدید / Create Backup Now",
            command=self._handle_create_backup
        ).pack(side="left")

        ttk.Button(
            actions,
            text="بازگرداندن از بکاپ انتخاب شده / Restore Selected Backup",
            command=self._handle_restore
        ).pack(side="left", padx=10)

        ttk.Button(
            actions,
            text="حذف بکاپ انتخاب شده / Delete Selected Backup",
            command=self._handle_delete_backup
        ).pack(side="left", padx=10)

        ttk.Button(
            actions,
            text="تازه‌سازی / Refresh",
            command=self.refresh_list
        ).pack(side="left", padx=10)

        ttk.Button(
            actions,
            text="تغییر محل ذخیره بکاپ / Change Backup Folder",
            command=self._handle_change_folder
        ).pack(side="left", padx=10)

        self.folder_label = ttk.Label(
            self,
            text=f"پوشه بکاپ / Backup folder: {self.backups_dir}",
            font=("Segoe UI", 8, "italic"),
            foreground="#666666"
        )
        self.folder_label.pack(anchor="w")

    def _build_list(self):
        ttk.Label(
            self,
            text="بکاپ‌های موجود / Existing Backups",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(15, 5))

        # --------------------------------------------------------------
        # List container
        # --------------------------------------------------------------
        # The scrollbar belongs only to the backup list.
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True)

        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        columns = ("filename", "created", "size")

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=14
        )

        headings = {
            "filename": "نام فایل / Filename",
            "created": "تاریخ / Created",
            "size": "حجم / Size"
        }

        widths = {
            "filename": 320,
            "created": 180,
            "size": 120
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(
                col,
                width=widths[col],
                anchor="center"
            )

        # Put the Treeview inside the list container
        self.tree.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        # --------------------------------------------------------------
        # Scrollbar ONLY for the backup list
        # --------------------------------------------------------------
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview
        )

        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )
    def _handle_change_folder(self):
        if not check_owner_action(
            self.current_user,
            "تغییر محل ذخیره بکاپ / Changing the backup save location"
        ):
            return

        chosen = filedialog.askdirectory(
            title="Select Backup Folder / انتخاب پوشه بکاپ"
        )
        if not chosen:
            return

        settings_service.set_backup_folder(chosen)
        self.backups_dir = self._get_backups_dir()
        self.folder_label.config(text=f"پوشه بکاپ / Backup folder: {self.backups_dir}")

        messagebox.showinfo(
            "Folder Changed",
            f"Future backups will now be saved to:\n{self.backups_dir}\n\n"
            f"Tip: point this at a synced folder (e.g. OneDrive) so backups "
            f"leave this computer automatically."
        )
        self.refresh_list()

    def refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        backup_files = sorted(
            self.backups_dir.glob("*.db"),
            key=os.path.getmtime,
            reverse=True
        )

        for f in backup_files:
            stat = f.stat()

            created = datetime.fromtimestamp(
                stat.st_mtime
            ).strftime("%Y-%m-%d %H:%M")

            size_kb = stat.st_size / 1024

            self.tree.insert(
                "",
                "end",
                values=(
                    f.name,
                    created,
                    f"{size_kb:.0f} KB"
                )
            )

    def _get_selected_filename(self):
        selection = self.tree.selection()

        if not selection:
            return None

        item = self.tree.item(selection[0])

        return item["values"][0]

    def _handle_create_backup(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")

        dest_path = (
            self.backups_dir /
            f"school_app_backup_{timestamp}.db"
        )

        try:
            self.db.backup_to(str(dest_path))

        except Exception as e:
            messagebox.showerror(
                "Backup Failed",
                f"Could not create backup:\n{e}"
            )
            return

        messagebox.showinfo(
            "Backup Created",
            f"Backup saved successfully:\n{dest_path.name}"
        )

        self.refresh_list()

    def _handle_restore(self):
        if not check_owner_action(
            self.current_user,
            "بازگرداندن بکاپ / Restoring a backup"
        ):
            return

        filename = self._get_selected_filename()

        if filename is None:
            messagebox.showwarning(
                "No Selection",
                "Select a backup from the list first."
            )
            return

        backup_path = self.backups_dir / filename

        confirm1 = messagebox.askyesno(
            "Confirm Restore",
            f"This will REPLACE the current database with:\n"
            f"{filename}\n\n"
            f"Any data added after this backup was made will be LOST.\n\n"
            f"A safety backup of the CURRENT database will be made "
            f"automatically before restoring. Continue?"
        )

        if not confirm1:
            return

        confirm2 = messagebox.askyesno(
            "Are You Absolutely Sure?",
            "This action cannot be undone from within the app.\n\n"
            "Proceed with restore?"
        )

        if not confirm2:
            return

        self.on_restore_requested(
            str(backup_path)
        )

    def _handle_delete_backup(self):
        if not check_owner_action(
            self.current_user,
            "حذف فایل بکاپ / Deleting a backup file"
        ):
            return

        filename = self._get_selected_filename()

        if filename is None:
            messagebox.showwarning(
                "No Selection",
                "Select a backup from the list first."
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete backup file '{filename}'?\n"
            "This cannot be undone."
        )

        if not confirm:
            return

        backup_path = self.backups_dir / filename

        try:
            backup_path.unlink()

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not delete backup file:\n{e}"
            )
            return

        messagebox.showinfo(
            "Deleted",
            "Backup file deleted."
        )

        self.refresh_list()