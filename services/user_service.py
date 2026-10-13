"""
services/user_service.py

Account management for the school owner: view existing users, create
manager accounts, delete manager accounts. Deliberately blocks
deleting the last remaining owner account or a user deleting their
own logged-in account, so nobody can accidentally lock everyone out.
"""


def get_all_users(db):
    return db.fetchall("SELECT id, username, role, created_at FROM users ORDER BY role, username;")


def get_user_by_id(db, user_id: int):
    return db.fetchone("SELECT * FROM users WHERE id = ?;", (user_id,))


def count_owners(db) -> int:
    row = db.fetchone("SELECT COUNT(*) AS cnt FROM users WHERE role IN ('owner', 'admin');")
    return row["cnt"]


def add_manager_user(db, username, password):
    if not username or not username.strip():
        raise ValueError("Username is required.")
    if not password or len(password) < 4:
        raise ValueError("Password must be at least 4 characters.")

    existing = db.fetchone("SELECT id FROM users WHERE username = ?;", (username.strip(),))
    if existing:
        raise ValueError("This username already exists.")

    return db.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, 'manager');",
        (username.strip(), password)
    )


def delete_user(db, user_id: int, current_user_id: int):
    target = get_user_by_id(db, user_id)
    if target is None:
        raise ValueError("User not found.")

    if target["id"] == current_user_id:
        raise ValueError("You cannot delete your own currently logged-in account.")

    if target["role"] in ("owner", "admin") and count_owners(db) <= 1:
        raise ValueError("Cannot delete the last remaining owner account.")

    db.execute("DELETE FROM users WHERE id = ?;", (user_id,))
def change_own_credentials(db, user_id, current_password, new_username, new_password):
    """
    Lets a logged-in user (owner or manager) change their OWN username
    and/or password only - never someone else's. Requires the current
    password to be entered correctly first, as a basic safeguard.
    Leaving new_username or new_password blank keeps the existing
    value for that field. Returns the final username (for the caller
    to show in a confirmation message).
    """
    user = get_user_by_id(db, user_id)
    if user is None:
        raise ValueError("Account not found.")

    if user["password"] != current_password:
        raise ValueError("Current password is incorrect.")

    final_username = user["username"]
    if new_username and new_username.strip():
        candidate = new_username.strip()
        if candidate != user["username"]:
            existing = db.fetchone(
                "SELECT id FROM users WHERE username = ? AND id != ?;",
                (candidate, user_id)
            )
            if existing:
                raise ValueError("This username is already taken.")
        final_username = candidate

    final_password = user["password"]
    if new_password and new_password.strip():
        if len(new_password) < 4:
            raise ValueError("New password must be at least 4 characters.")
        final_password = new_password

    db.execute(
        "UPDATE users SET username = ?, password = ? WHERE id = ?;",
        (final_username, final_password, user_id)
    )

    return final_username