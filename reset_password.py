"""
Temporary recovery script - NOT part of the app.
Run this once to see all accounts and reset a forgotten password.
Delete this file when you're done with it.
"""

from database import Database

db = Database()

print("--- All accounts in this database ---")
users = db.fetchall("SELECT id, username, role FROM users ORDER BY id;")
for u in users:
    print(f"  id={u['id']}  username='{u['username']}'  role={u['role']}")

if not users:
    print("  (no accounts found)")
    db.close()
    exit()

print()
target_id = input("Enter the id of the account to reset: ").strip()
new_password = input("Enter the new password (min 4 characters): ").strip()

if len(new_password) < 4:
    print("Password must be at least 4 characters. Aborting.")
    db.close()
    exit()

db.execute("UPDATE users SET password = ? WHERE id = ?;", (new_password, target_id))

print(f"\nDone. Password for account id={target_id} has been reset.")
print("You can now log in with that username and the new password.")

db.close()