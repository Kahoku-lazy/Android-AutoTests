"""Helpers for AI assistant chat file uploads under data/uploads/."""

from __future__ import annotations

import logging
import time

from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

UPLOAD_DIR = settings.BASE_DIR / "data" / "uploads"
DEFAULT_MAX_AGE_SECONDS = int(getattr(settings, "UPLOAD_CLEANUP_MAX_AGE_DAYS", 7) * 24 * 3600)


def ensure_upload_dir() -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


def safe_upload_path(filepath: Path) -> bool:
    """Return True if path is a regular file inside UPLOAD_DIR."""
    try:
        resolved = filepath.resolve()
        root = UPLOAD_DIR.resolve()
        resolved.relative_to(root)
    except (ValueError, OSError):
        return False
    return resolved.is_file()


def remove_upload_file(filepath: Path | str) -> bool:
    """Delete one upload file if it lies under UPLOAD_DIR."""
    path = Path(filepath)
    if not safe_upload_path(path):
        return False
    try:
        path.unlink(missing_ok=True)
        return True
    except OSError as exc:
        logger.warning("Failed to delete upload %s: %s", path, exc)
        return False


def cleanup_upload_dir(
    max_age_seconds: int | None = None,
    *,
    dry_run: bool = False,
) -> dict:
    """Remove upload files older than max_age_seconds (default from settings)."""
    ensure_upload_dir()
    age = max_age_seconds if max_age_seconds is not None else DEFAULT_MAX_AGE_SECONDS
    cutoff = time.time() - max(0, age)
    deleted = 0
    bytes_freed = 0
    errors: list[str] = []

    for entry in UPLOAD_DIR.iterdir():
        if not entry.is_file():
            continue
        try:
            if entry.stat().st_mtime >= cutoff:
                continue
            size = entry.stat().st_size
            if dry_run:
                deleted += 1
                bytes_freed += size
                continue
            entry.unlink()
            deleted += 1
            bytes_freed += size
        except OSError as exc:
            errors.append(f"{entry.name}: {exc}")

    return {
        "deleted": deleted,
        "bytes_freed": bytes_freed,
        "dry_run": dry_run,
        "max_age_seconds": age,
        "errors": errors,
    }
