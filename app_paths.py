"""Operating-system appropriate locations used by Expense App Desktop."""

import os
import sys
from pathlib import Path


APP_DIR_NAME = "expense-app-desktop"


def user_data_dir() -> Path:
    """Return the directory used for rules and backups."""
    if sys.platform == "win32":
        configured_base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        base = Path(configured_base) if configured_base else Path.home()
        return base / "Expense App Desktop"

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Expense App Desktop"

    configured_base = os.environ.get("XDG_DATA_HOME")
    base = Path(configured_base) if configured_base else Path.home() / ".local" / "share"
    return base / APP_DIR_NAME


def user_cache_dir() -> Path:
    """Return the directory used for launcher logs and its lock file."""
    if sys.platform == "win32":
        return user_data_dir() / "logs"

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "Expense App Desktop"

    configured_base = os.environ.get("XDG_CACHE_HOME")
    base = Path(configured_base) if configured_base else Path.home() / ".cache"
    return base / APP_DIR_NAME


def documents_dir() -> Path:
    """Return the standard Documents directory without creating it."""
    if sys.platform == "win32":
        user_profile = os.environ.get("USERPROFILE")
        return (Path(user_profile) if user_profile else Path.home()) / "Documents"
    return Path.home() / "Documents"
