import logging
from unittest.mock import MagicMock, patch

from app.core.logging import (
    SensitiveDataFilter,
    SensitiveDataProcessor,
    configure_logging,
    get_logger,
    sanitize_dict,
)


def test_sensitive_data_filter_edge_cases():
    """Test SensitiveDataFilter with edge cases"""
    log_filter = SensitiveDataFilter()
    # Use simple assignment without quotes to avoid regex grouping issues in test validation
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="api_key=secret token=xyz password=123",
        args=(),
        exc_info=None,
    )

    # Test message filtering
    assert log_filter.filter(record) is True
    # The filter replaces the whole pattern match with key=***REDACTED***
    assert "api_key=***REDACTED***" in record.msg
    assert "token=***REDACTED***" in record.msg
    assert "password=***REDACTED***" in record.msg

    # Test args filtering
    record.msg = "User login failed: %s"
    record.args = ("password=secret",)
    log_filter.filter(record)
    assert "password=***REDACTED***" in record.args[0]

    # Test non-string args
    record.args = (123, {"key": "val"})
    log_filter.filter(record)
    assert record.args == (123, {"key": "val"})


def test_sanitize_dict_edge_cases():
    """Test sanitize_dict with comprehensive edge cases"""
    data = {
        "normal": "value",
        "api_key": "secret123",
        "nested": {"password": "pass", "deep": {"secret": "hidden"}},
        "list_of_dicts": [{"token": "abc"}, {"safe": "data"}],
        "list_of_values": [1, 2, 3],
        "mixed": {"auth": "bearer token", "number": 42},
    }

    sanitized = sanitize_dict(data)

    assert sanitized["normal"] == "value"
    assert sanitized["api_key"] == "***REDACTED***"
    assert sanitized["nested"]["password"] == "***REDACTED***"
    assert sanitized["nested"]["deep"]["secret"] == "***REDACTED***"
    assert sanitized["list_of_dicts"][0]["token"] == "***REDACTED***"
    assert sanitized["list_of_dicts"][1]["safe"] == "data"
    assert sanitized["list_of_values"] == [1, 2, 3]
    assert sanitized["mixed"]["auth"] == "***REDACTED***"
    assert sanitized["mixed"]["number"] == 42


def test_sensitive_data_processor():
    """Test SensitiveDataProcessor for structlog"""
    processor = SensitiveDataProcessor()
    event_dict = {"event": "user_action", "password": "secret_password", "meta": {"api_key": "12345"}}

    processed = processor(None, None, event_dict)

    assert processed["event"] == "user_action"
    assert processed["password"] == "***REDACTED***"
    assert processed["meta"]["api_key"] == "***REDACTED***"


def test_configure_logging_levels():
    """Test configure_logging with different levels"""
    with patch("logging.getLogger") as mock_get_logger:
        root_logger = MagicMock()
        mock_get_logger.return_value = root_logger

        # Test DEBUG
        configure_logging("DEBUG")
        root_logger.setLevel.assert_called_with("DEBUG")

        # Test ERROR
        configure_logging("ERROR")
        root_logger.setLevel.assert_called_with("ERROR")


def test_get_logger():
    """Test get_logger wrapper"""
    logger = get_logger("test_logger")
    # Verify it has structlog-like methods
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")
    assert hasattr(logger, "bind")
