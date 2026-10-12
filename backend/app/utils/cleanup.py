"""
Cleanup and resource management utilities.
Handles purging of expired session artifacts and temporary files.
"""

import shutil
from pathlib import Path
from typing import Optional
from app.core.config import settings
from app.core.logging import logger


def cleanup_session_storage(session_id: str, storage_root: Optional[Path] = None) -> bool:
    """
    Remove all temporary files and directory allocated to a session.
    """
    if not session_id:
        return False

    base_dir = storage_root or settings.TEMP_STORAGE_DIR
    target_dir = base_dir / session_id

    if target_dir.exists() and target_dir.is_dir():
        try:
            shutil.rmtree(target_dir)
            logger.info(f"Cleaned up session storage directory: {target_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to clean up storage for session {session_id}: {e}")
            return False
    return False


def purge_expired_directories(max_age_seconds: int = 3600, storage_root: Optional[Path] = None) -> int:
    """
    Scan storage root and purge directories that exceed max age.
    Returns count of removed directories.
    """
    import time
    base_dir = storage_root or settings.TEMP_STORAGE_DIR
    if not base_dir.exists():
        return 0

    now = time.time()
    purged = 0

    for item in base_dir.iterdir():
        if item.is_dir() and item.name != ".gitkeep":
            try:
                mtime = item.stat().st_mtime
                if now - mtime > max_age_seconds:
                    shutil.rmtree(item)
                    purged += 1
                    logger.info(f"Purged expired storage: {item}")
            except Exception as e:
                logger.warning(f"Error purging directory {item}: {e}")
    return purged
