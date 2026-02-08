"""Temporary image cleanup service [REQ-1.1.3]

This service automatically deletes expired extracted images to free up disk space.
"""

import json
import shutil
from datetime import UTC, datetime
from typing import Optional

import structlog
from apscheduler.schedulers.background import BackgroundScheduler

from app.config import EXTRACTED_IMAGES_DIR

logger = structlog.get_logger(__name__)


class ImageCleanupService:
    """Auto-delete expired extracted images.

    Runs a background scheduler that checks for expired extraction directories
    every hour and removes them.
    """

    _instance: Optional["ImageCleanupService"] = None

    def __init__(self):
        """Initialize the cleanup service."""
        self.scheduler = BackgroundScheduler()
        self.logger = structlog.get_logger(__name__)

    @classmethod
    def get_instance(cls) -> "ImageCleanupService":
        """Get singleton instance of the cleanup service."""
        if cls._instance is None:
            cls._instance = ImageCleanupService()
        return cls._instance

    def start(self) -> None:
        """Start hourly cleanup job."""
        if self.scheduler.running:
            self.logger.info("cleanup_service_already_running")
            return

        self.scheduler.add_job(
            self._cleanup_expired,
            "interval",
            hours=1,
            id="image_cleanup",
            replace_existing=True,
        )
        self.scheduler.start()
        self.logger.info("image_cleanup_service_started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self.logger.info("image_cleanup_service_stopped")

    def cleanup_now(self) -> int:
        """Run cleanup immediately and return count of deleted directories."""
        return self._cleanup_expired()

    def _cleanup_expired(self) -> int:
        """Delete expired extraction directories.

        Returns:
            Number of directories deleted
        """
        if not EXTRACTED_IMAGES_DIR.exists():
            return 0

        now = datetime.now(UTC).replace(tzinfo=None)
        deleted_count = 0

        for extraction_dir in EXTRACTED_IMAGES_DIR.iterdir():
            if not extraction_dir.is_dir():
                continue

            metadata_path = extraction_dir / "metadata.json"
            if not metadata_path.exists():
                # No metadata - delete if older than 24 hours
                try:
                    mtime = datetime.fromtimestamp(extraction_dir.stat().st_mtime)
                    if (now - mtime).total_seconds() > 24 * 3600:
                        shutil.rmtree(extraction_dir)
                        deleted_count += 1
                except Exception as e:
                    self.logger.warning(
                        "cleanup_no_metadata_error",
                        path=str(extraction_dir),
                        error=str(e),
                    )
                continue

            try:
                metadata = json.loads(metadata_path.read_text())
                expires_at = datetime.fromisoformat(metadata["expires_at"])

                if now > expires_at:
                    shutil.rmtree(extraction_dir)
                    deleted_count += 1
                    self.logger.debug(
                        "extraction_deleted",
                        path=str(extraction_dir),
                        expired_at=metadata["expires_at"],
                    )
            except Exception as e:
                self.logger.warning(
                    "cleanup_error",
                    path=str(extraction_dir),
                    error=str(e),
                )

        if deleted_count > 0:
            self.logger.info("cleanup_completed", deleted=deleted_count)

        return deleted_count


# Global instance for easy access
cleanup_service = ImageCleanupService.get_instance()
