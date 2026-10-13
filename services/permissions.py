"""
services/permissions.py

Centralized role-based access control.

Two roles:
  - "owner" (also "admin", kept for accounts created before this
    feature existed) - full access to everything.
  - "manager" - day-to-day data entry, blocked from destructive or
    financial-policy actions (see the module docstrings in payments,
    fees, library, backup, and course_payment services for exactly
    what's restricted).

Every screen that needs to lock a button/action for managers calls
check_owner_action(current_user, "description") before performing the
action, instead of re-implementing this logic per screen.
"""

from tkinter import messagebox

OWNER_ROLES = ("owner", "admin")  # "admin" = accounts created before roles existed
MANAGER_ROLE = "manager"


def is_owner(current_user) -> bool:
    if current_user is None:
        return False
    return current_user["role"] in OWNER_ROLES


def check_owner_action(current_user, action_description: str) -> bool:
    """
    Returns True if the action may proceed. If not, shows a clear
    bilingual message and returns False - callers should stop
    immediately when this returns False.
    """
    if is_owner(current_user):
        return True

    messagebox.showwarning(
        "دسترسی محدود / Access Restricted",
        f"{action_description}\n\n"
        f"این عملیات فقط برای مالک مکتب مجاز است.\n"
        f"This action is restricted to the school owner only."
    )
    return False