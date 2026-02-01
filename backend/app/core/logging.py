"""Structured logging configuration module"""

import logging
import re

import structlog
from pythonjsonlogger.json import JsonFormatter


class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive data from logs"""

    # Sensitive data patterns
    SENSITIVE_PATTERNS = [
        (re.compile(r"api[_-]?key[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_-]+)", re.IGNORECASE), "api_key=***REDACTED***"),
        (re.compile(r"token[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_.-]+)", re.IGNORECASE), "token=***REDACTED***"),
        (re.compile(r"password[\"']?\s*[:=]\s*[\"']?([^\s\"']+)", re.IGNORECASE), "password=***REDACTED***"),
        (re.compile(r"secret[\"']?\s*[:=]\s*[\"']?([^\s\"']+)", re.IGNORECASE), "secret=***REDACTED***"),
        (
            re.compile(r"authorization:\s*bearer\s+([a-zA-Z0-9_.-]+)", re.IGNORECASE),
            "authorization: bearer ***REDACTED***",
        ),
        # IBM Watson API Key pattern
        (re.compile(r"[a-zA-Z0-9_-]{44,}", re.IGNORECASE), "***REDACTED_KEY***"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter sensitive data from log records

        Args:
            record: Log record

        Returns:
            Always True (message is modified and passed through)
        """
        if hasattr(record, "msg") and isinstance(record.msg, str):
            message = record.msg
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                message = pattern.sub(replacement, message)
            record.msg = message

        # Also process args
        if hasattr(record, "args") and record.args:
            sanitized_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    for pattern, replacement in self.SENSITIVE_PATTERNS:
                        arg = pattern.sub(replacement, arg)
                sanitized_args.append(arg)
            record.args = tuple(sanitized_args)

        return True


def sanitize_dict(data: dict) -> dict:
    """Redact sensitive data from dictionary

    Args:
        data: Dictionary to sanitize

    Returns:
        Sanitized dictionary
    """
    SENSITIVE_KEYS = {
        "api_key",
        "apikey",
        "api-key",
        "token",
        "access_token",
        "refresh_token",
        "password",
        "passwd",
        "pwd",
        "secret",
        "secret_key",
        "authorization",
        "auth",
        "ibm_api_key",
        "ibm_project_id",
    }

    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower().replace("_", "").replace("-", "")

        # Mask if sensitive key
        if any(sensitive in key_lower for sensitive in SENSITIVE_KEYS):
            sanitized[key] = "***REDACTED***"
        # Recursively process nested dictionaries
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        # Process each item if list
        elif isinstance(value, list):
            sanitized[key] = [sanitize_dict(item) if isinstance(item, dict) else item for item in value]
        else:
            sanitized[key] = value

    return sanitized


class SensitiveDataProcessor:
    """Sensitive data redaction processor for structlog"""

    def __call__(self, logger, method_name, event_dict):
        """Redact sensitive data from event dictionary"""
        return sanitize_dict(event_dict)


def configure_logging(level: str = "INFO"):
    """Configure structured logging

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """

    # structlog configuration
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            SensitiveDataProcessor(),  # Add sensitive data filter
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Standard logging configuration
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(SensitiveDataFilter())  # Add sensitive data filter

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)


def get_logger(name: str):
    """Get structured logger

    Args:
        name: Logger name (usually __name__)

    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)
