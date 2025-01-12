import os
import platformdirs
from typing import Optional
from pathlib import Path


def get_app_data_dir() -> Path:
    """Get the platform-specific application data directory for bwilcd"""
    return Path(platformdirs.user_data_dir("bwilcd"))


def get_downloads_dir() -> Path:
    """Get the platform-specific downloads directory for bwilcd"""
    base_dir = get_app_data_dir() / "downloads"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def ensure_dir_exists(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary"""
    path.mkdir(parents=True, exist_ok=True)


def format_size(size_bytes: int) -> str:
    """Format a size in bytes to a human readable string"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
