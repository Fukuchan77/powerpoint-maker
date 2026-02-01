"""File upload validation utilities"""

import os
import re
from typing import Set

from fastapi import HTTPException, UploadFile

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
ALLOWED_EXTENSIONS: Set[str] = {".pptx"}
ALLOWED_MIME_TYPES: Set[str] = {"application/vnd.openxmlformats-officedocument.presentationml.presentation"}

# Magic bytes for file type validation
# PPTX files are ZIP archives, so they start with PK\x03\x04
MAGIC_BYTES = {
    ".pptx": [
        b"PK\x03\x04",  # ZIP file signature (PPTX is a ZIP archive)
    ]
}


async def validate_template_file(file: UploadFile) -> bytes:
    """
    Validate uploaded template file

    Args:
        file: Uploaded file from FastAPI

    Returns:
        File content as bytes

    Raises:
        HTTPException: If validation fails
    """
    # Check file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = "." + file.filename.split(".")[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, detail=f"Invalid file type. Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed"
        )

    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid content type: {file.content_type}")

    # Read and check file size
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        size_mb = file_size / (1024 * 1024)
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"File too large ({size_mb:.2f}MB). Maximum size is {max_mb}MB")

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    # Validate magic bytes (file signature)
    if file_ext in MAGIC_BYTES:
        magic_bytes_list = MAGIC_BYTES[file_ext]
        is_valid_magic = any(content.startswith(magic) for magic in magic_bytes_list)

        if not is_valid_magic:
            raise HTTPException(
                status_code=400, detail=f"Invalid file format. File does not match expected {file_ext} signature"
            )

    # Reset file pointer for later use
    await file.seek(0)

    return content


def get_safe_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Get basename to prevent path traversal
    filename = os.path.basename(filename)

    # Remove any path separators and parent directory references
    filename = filename.replace("\\", "")
    filename = filename.replace("/", "")
    filename = filename.replace("..", "")

    # Remove any non-alphanumeric characters except dots, hyphens, underscores
    filename = re.sub(r"[^\w\s.-]", "", filename)

    # Replace spaces with underscores
    filename = filename.replace(" ", "_")

    # Remove any remaining double dots (from consecutive dots after cleaning)
    while ".." in filename:
        filename = filename.replace("..", ".")

    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[: 255 - len(ext)] + ext

    return filename
