"""Custom exceptions for PPTX Enhancement feature.

Implements REQ-5.1, REQ-5.2, REQ-5.3
"""


class ExtractionError(Exception):
    """Content extraction error [REQ-5.1]

    Raised when content cannot be extracted from a PPTX file.
    """

    pass


class MarkdownSyntaxError(Exception):
    """Markdown syntax error [REQ-5.2]

    Raised when invalid Markdown syntax is detected.

    Attributes:
        line: Error line number
        column: Error column number
        message: User-friendly error message
    """

    def __init__(self, line: int, column: int, message: str):
        self.line = line
        self.column = column
        self.message = message
        super().__init__(f"Line {line}, Column {column}: {message}")


class ImageExpiredError(Exception):
    """Image expired error [REQ-5.3]

    Raised when attempting to access an expired or deleted extracted image.
    """

    pass
