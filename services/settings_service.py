"""
services/settings_service.py

Small persistent app settings, stored in a JSON file next to the app
(separate from the SQLite database, since these are app-level
preferences, not school data). Currently used for: a custom backup
save location, so backups can be pointed at a synced folder like
OneDrive instead of always sitting on the same computer as the app.
"""

import json
from pathlib import Path


def _get_settings_path() -> Path:
    project_root = Path(__file__).resolve().parent.parent
    return project_root / "app_settings.json"


def _load_settings() -> dict:
    path = _get_settings_path()
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_settings(data: dict):
    path = _get_settings_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_backup_folder() -> str:
    """Custom backup folder, or '' if the owner hasn't set one (use the default)."""
    return _load_settings().get("backup_folder", "")


def set_backup_folder(folder_path: str):
    settings = _load_settings()
    settings["backup_folder"] = folder_path
    _save_settings(settings)