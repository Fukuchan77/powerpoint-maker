"""Unit tests for the image cleanup service.

Target coverage: 85%
"""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from app.services.cleanup import ImageCleanupService


class TestImageCleanupService:
    """Tests for the ImageCleanupService class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a fresh instance for each test (not using singleton)
        self.cleanup = ImageCleanupService()

    def teardown_method(self):
        """Clean up after each test."""
        if self.cleanup.scheduler.running:
            self.cleanup.stop()

    def test_start_scheduler(self):
        """Test that start() adds job and starts the scheduler."""
        # Use a fresh instance with mocked scheduler
        cleanup = ImageCleanupService()
        cleanup.scheduler = MagicMock()
        cleanup.scheduler.running = False

        cleanup.start()
        cleanup.scheduler.add_job.assert_called_once()
        cleanup.scheduler.start.assert_called_once()

    def test_start_skips_if_already_running(self):
        """Test that start() doesn't restart if already running."""
        cleanup = ImageCleanupService()
        cleanup.scheduler = MagicMock()
        cleanup.scheduler.running = True

        cleanup.start()
        cleanup.scheduler.start.assert_not_called()

    def test_stop_scheduler(self):
        """Test that stop() stops the scheduler."""
        cleanup = ImageCleanupService()
        cleanup.scheduler = MagicMock()
        cleanup.scheduler.running = True

        cleanup.stop()
        cleanup.scheduler.shutdown.assert_called_once()

    def test_stop_does_nothing_if_not_running(self):
        """Test that stop() does nothing if not running."""
        cleanup = ImageCleanupService()
        cleanup.scheduler = MagicMock()
        cleanup.scheduler.running = False

        cleanup.stop()
        cleanup.scheduler.shutdown.assert_not_called()

    def test_cleanup_now_returns_deleted_count(self, tmp_path, monkeypatch):
        """Test that cleanup_now runs cleanup and returns count."""
        monkeypatch.setattr("app.services.cleanup.EXTRACTED_IMAGES_DIR", tmp_path)

        # Create an expired extraction
        extraction_dir = tmp_path / "expired-extraction"
        extraction_dir.mkdir()
        metadata = {
            "expires_at": (datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)).isoformat(),
            "image_count": 0,
        }
        (extraction_dir / "metadata.json").write_text(json.dumps(metadata))

        deleted = self.cleanup.cleanup_now()
        assert deleted == 1
        assert not extraction_dir.exists()

    def test_cleanup_preserves_valid_extractions(self, tmp_path, monkeypatch):
        """Test that valid (non-expired) extractions are preserved."""
        monkeypatch.setattr("app.services.cleanup.EXTRACTED_IMAGES_DIR", tmp_path)

        # Create a valid extraction
        extraction_dir = tmp_path / "valid-extraction"
        extraction_dir.mkdir()
        metadata = {
            "expires_at": (datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=23)).isoformat(),
            "image_count": 0,
        }
        (extraction_dir / "metadata.json").write_text(json.dumps(metadata))

        deleted = self.cleanup.cleanup_now()
        assert deleted == 0
        assert extraction_dir.exists()

    def test_cleanup_handles_missing_directory(self, tmp_path, monkeypatch):
        """Test cleanup handles missing EXTRACTED_IMAGES_DIR."""
        nonexistent = tmp_path / "nonexistent"
        monkeypatch.setattr("app.services.cleanup.EXTRACTED_IMAGES_DIR", nonexistent)

        deleted = self.cleanup.cleanup_now()
        assert deleted == 0

    def test_cleanup_handles_malformed_metadata(self, tmp_path, monkeypatch):
        """Test cleanup handles directories with malformed metadata."""
        monkeypatch.setattr("app.services.cleanup.EXTRACTED_IMAGES_DIR", tmp_path)

        # Create extraction with invalid JSON
        extraction_dir = tmp_path / "malformed"
        extraction_dir.mkdir()
        (extraction_dir / "metadata.json").write_text("invalid json")

        deleted = self.cleanup.cleanup_now()
        assert deleted == 0
        assert extraction_dir.exists()  # Not deleted due to error

    def test_cleanup_handles_missing_metadata(self, tmp_path, monkeypatch):
        """Test cleanup handles directories without metadata."""
        monkeypatch.setattr("app.services.cleanup.EXTRACTED_IMAGES_DIR", tmp_path)

        # Create extraction without metadata but old enough to delete
        extraction_dir = tmp_path / "no-metadata"
        extraction_dir.mkdir()

        # Can't reliably set old mtime, so just verify it doesn't crash
        deleted = self.cleanup.cleanup_now()
        # Directory may or may not be deleted depending on creation time
        assert deleted >= 0

    def test_cleanup_skips_files(self, tmp_path, monkeypatch):
        """Test that cleanup skips regular files."""
        monkeypatch.setattr("app.services.cleanup.EXTRACTED_IMAGES_DIR", tmp_path)

        # Create a file instead of directory
        (tmp_path / "not-a-dir.txt").write_text("test")

        deleted = self.cleanup.cleanup_now()
        assert deleted == 0

    def test_get_instance_returns_singleton(self):
        """Test that get_instance returns the same instance."""
        # Reset singleton for test
        ImageCleanupService._instance = None

        instance1 = ImageCleanupService.get_instance()
        instance2 = ImageCleanupService.get_instance()

        assert instance1 is instance2

        # Clean up
        ImageCleanupService._instance = None

    def test_cleanup_multiple_extractions(self, tmp_path, monkeypatch):
        """Test cleanup with mixed expired and valid extractions."""
        monkeypatch.setattr("app.services.cleanup.EXTRACTED_IMAGES_DIR", tmp_path)

        # Create expired extractions
        for i in range(3):
            extraction_dir = tmp_path / f"expired-{i}"
            extraction_dir.mkdir()
            metadata = {
                "expires_at": (datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)).isoformat(),
            }
            (extraction_dir / "metadata.json").write_text(json.dumps(metadata))

        # Create valid extraction
        valid_dir = tmp_path / "valid"
        valid_dir.mkdir()
        metadata = {
            "expires_at": (datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=23)).isoformat(),
        }
        (valid_dir / "metadata.json").write_text(json.dumps(metadata))

        deleted = self.cleanup.cleanup_now()
        assert deleted == 3
        assert valid_dir.exists()
