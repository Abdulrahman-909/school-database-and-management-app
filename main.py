"""
main.py

Entry point for the School Management application.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import traceback
import ctypes
from pathlib import Path
from datetime import datetime


def _fix_windows_dpi_scaling():
    """
    Tells Windows this app handles its own screen scaling. Without
    this, Windows DPI scaling (very common on external/large monitors
    set to 125%-150%) stretches the whole Tkinter window, making
    everything look zoomed in. Safe no-op on non-Windows systems.
    """
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # Windows 8.1+
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()  # Windows Vista/7 fallback
        except Exception:
            pass  # not on Windows, or API unavailable - ignore


_fix_windows_dpi_scaling()

from database import Database, DatabaseError
from ui.login import LoginFrame
from ui.dashboard import DashboardFrame
from ui.students import StudentsFrame
from ui.teachers import TeachersFrame
from ui.classes import ClassesFrame
from ui.fees import FeeStructureFrame
from ui.payments import PaymentsFrame
from ui.finance import FinanceFrame
from ui.salaries import SalariesFrame
from ui.library import LibraryFrame
from ui.reports import ReportsFrame
from ui.excel_export import ExcelExportFrame
from ui.backup import BackupFrame
from ui.courses import CoursesFrame
from ui.users import UsersFrame
from ui.rosters import RostersFrame
from ui.account import AccountFrame

APP_TITLE = "سیستم مدیریت مکتب - School Management System"
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 750


def log_crash(exc_type, exc_value, exc_tb):
    try:
        project_root = Path(__file__).resolve().parent
        log_path = project_root / "data" / "crash_log.txt"
        log_path.parent.mkdir(exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n\n=== Crash at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
    except Exception:
        pass

    try:
        messagebox.showerror(
            "Unexpected Error",
            "An unexpected error occurred and the application must close.\n\n"
            "Details were saved to data/crash_log.txt - please share this "
            "file if you report the problem."
        )
    except Exception:
        pass


sys.excepthook = log_crash


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Apply scaling fix immediately after Tk initializes, before
        # ANY widget (including Login) is built or shown.
        try:
            self.tk.call('tk', 'scaling', 1.0)
        except Exception:
            pass

        self.title(APP_TITLE)

        # Force Tkinter's internal scaling to a known, sane value
        # (96 DPI baseline = scaling factor 1.0), regardless of what
        # Windows reports. This is a stronger override than relying on
        # SetProcessDpiAwareness alone - it directly controls how large
        # Tkinter draws fonts/widgets, independent of the monitor's
        # Windows display scaling percentage.
        try:
            self.tk.call('tk', 'scaling', 1.0)
        except Exception:
            pass

        # Size the window relative to the ACTUAL screen instead of a
        # fixed 1100x750, so it looks reasonable on both small laptop
        # screens and large external monitors.
        # Responsive sizing: the window is a comfortable percentage of
        # the actual screen (not maximized, not a fixed 1100x750),
        # centered. Capped so it can never exceed the real screen size
        # reported by Windows, which is the safety net that matters
        # most on smaller/older screens.
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        # Cap at a comfortable fixed maximum (WINDOW_WIDTH/HEIGHT) on
        # large screens, or 75% of the screen on smaller ones -
        # whichever is smaller. This avoids a huge window with empty
        # space on wide monitors, while remaining fully responsive
        # (never exceeding the actual screen) on small/older screens.
        window_width = min(WINDOW_WIDTH, int(screen_width * 0.75))
        window_height = min(WINDOW_HEIGHT, int(screen_height * 0.75))
        x_pos = (screen_width - window_width) // 2
        y_pos = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")
        self.minsize(950, 600)

        self.current_user = None

        try:
            self.db = Database()
        except DatabaseError as e:
            messagebox.showerror(
                "Database Error",
                f"The application could not start because the database "
                f"could not be opened.\n\nDetails:\n{e}"
            )
            self.destroy()
            sys.exit(1)

        style = ttk.Style(self)
        style.theme_use("clam")

        # Bump the default font size app-wide, so text reads
        # comfortably on typical screens without needing to touch
        # every individual screen's font settings one by one.
        default_font = ("Segoe UI", 11)
        self.option_add("*Font", default_font)
        style.configure(".", font=default_font)
        style.configure("Treeview", font=default_font, rowheight=26)
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"))

        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.show_login()

    def _clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_login(self):
        self.current_user = None
        self._clear_container()
        login_frame = LoginFrame(self.container, self.db, self.on_login_success)
        login_frame.pack(expand=True)

    def on_login_success(self, user):
        self.current_user = user
        self.show_dashboard()

    def show_dashboard(self):
        self._clear_container()
        DashboardFrame(
            self.container,
            self.db,
            self.current_user,
            on_logout=self.show_login,
            on_navigate=self.handle_navigate
        )

    def handle_navigate(self, module_key, label):
        if module_key == "students":
            self.show_students()
            return
        if module_key == "teachers":
            self.show_teachers()
            return
        if module_key == "classes":
            self.show_classes()
            return
        if module_key == "rosters":
            self.show_rosters()
            return
        if module_key == "fees":
            self.show_fees()
            return
        if module_key == "payments":
            self.show_payments()
            return
        if module_key == "finance":
            self.show_finance()
            return
        if module_key == "salaries":
            self.show_salaries()
            return
        if module_key == "library":
            self.show_library()
            return
        if module_key == "reports":
            self.show_reports()
            return
        if module_key == "excel_export":
            self.show_excel_export()
            return
        if module_key == "backup":
            self.show_backup()
            return
        if module_key == "courses":
            self.show_courses()
            return
        if module_key == "users":
            self.show_users()
            return
        if module_key == "account":
            self.show_account()
            return

        messagebox.showinfo("Not Built Yet", f"'{label}' has not been built yet.")

    def show_students(self):
        self._clear_container()
        StudentsFrame(self.container, self.db, on_back=self.show_dashboard)

    def show_teachers(self):
        self._clear_container()
        TeachersFrame(self.container, self.db, on_back=self.show_dashboard)

    def show_classes(self):
        self._clear_container()
        ClassesFrame(self.container, self.db, on_back=self.show_dashboard)

    def show_rosters(self):
        self._clear_container()
        RostersFrame(self.container, self.db, on_back=self.show_dashboard)

    def show_fees(self):
        self._clear_container()
        FeeStructureFrame(self.container, self.db, self.current_user, on_back=self.show_dashboard)

    def show_payments(self):
        self._clear_container()
        PaymentsFrame(self.container, self.db, self.current_user, on_back=self.show_dashboard)

    def show_finance(self):
        self._clear_container()
        FinanceFrame(self.container, self.db, on_back=self.show_dashboard)

    def show_salaries(self):
        self._clear_container()
        SalariesFrame(self.container, self.db, on_back=self.show_dashboard)

    def show_library(self):
        self._clear_container()
        LibraryFrame(self.container, self.db, self.current_user, on_back=self.show_dashboard)

    def show_reports(self):
        self._clear_container()
        ReportsFrame(self.container, self.db, on_back=self.show_dashboard)

    def show_excel_export(self):
        self._clear_container()
        ExcelExportFrame(self.container, self.db, on_back=self.show_dashboard)

    def show_backup(self):
        self._clear_container()
        BackupFrame(
            self.container, self.db, self.current_user,
            on_back=self.show_dashboard,
            on_restore_requested=self.handle_restore
        )

    def show_courses(self):
        self._clear_container()
        CoursesFrame(self.container, self.db, self.current_user, on_back=self.show_dashboard)

    def show_users(self):
        self._clear_container()
        UsersFrame(self.container, self.db, self.current_user, on_back=self.show_dashboard)

    def show_account(self):
        self._clear_container()
        AccountFrame(
            self.container, self.db, self.current_user,
            on_back=self.show_dashboard,
            on_credentials_changed=self.show_login
        )

    def handle_restore(self, backup_file_path):
        project_root = Path(__file__).resolve().parent
        backups_dir = project_root / "data" / "backups"
        backups_dir.mkdir(parents=True, exist_ok=True)
        safety_path = backups_dir / f"pre_restore_safety_{datetime.now().strftime('%Y-%m-%d_%H%M')}.db"

        try:
            self.db.backup_to(str(safety_path))
        except Exception as e:
            messagebox.showerror(
                "Restore Cancelled",
                f"Could not create a safety backup before restoring, so the "
                f"restore was cancelled to avoid data loss.\n\nDetails:\n{e}"
            )
            return

        try:
            self.db.restore_from(backup_file_path)
        except Exception as e:
            messagebox.showerror("Restore Failed", f"Restore failed:\n{e}")
            return

        messagebox.showinfo(
            "Restore Complete",
            f"Database restored successfully.\n\n"
            f"A safety backup of the previous database was saved as:\n{safety_path.name}\n\n"
            f"You will be returned to the login screen."
        )
        self.show_login()

    def on_close(self):
        try:
            self.db.close()
        except Exception as e:
            print(f"[WARNING] Error while closing database: {e}")
        self.destroy()


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()