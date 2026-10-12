"""
Security module for Supply and Demand Forecasting application.
Provides:
- Path traversal and filename sanitization
- CSV formula injection (DDE attack) neutralization
- Unguessable cryptographically secure token generation
"""

import re
import secrets
from typing import Any, List


def generate_secure_token(nbytes: int = 32) -> str:
    """Generate cryptographically secure hexadecimal token."""
    return secrets.token_hex(nbytes)


def sanitize_filename(filename: str, default: str = "dataset.csv") -> str:
    """
    Sanitize uploaded or exported filename to prevent path traversal
    and illegal filesystem characters.
    """
    if not filename or not isinstance(filename, str):
        return default

    # Remove any directory path components
    clean = filename.replace("\\", "/").split("/")[-1]
    # Replace dangerous or reserved characters
    clean = re.sub(r'[^a-zA-Z0-9_.\-]', '_', clean)
    clean = re.sub(r'_+', '_', clean).strip("._")

    if not clean:
        return default
    return clean[:100]


def is_safe_filename(filename: str) -> bool:
    """Validate that a filename contains no path traversal sequences or illegal characters."""
    if not filename or ".." in filename or "/" in filename or "\\" in filename:
        return False
    return bool(re.match(r'^[a-zA-Z0-9_\-.]+$', filename))


def sanitize_csv_cell(value: Any) -> str:
    """
    Neutralize CSV formula injection (DDE attacks).
    Spreadsheets execute formulas if a cell starts with =, +, -, @, \\t, or \\r.
    Prefixing with a single quote (') neutralizes execution.
    """
    if value is None:
        return ""
    val_str = str(value)
    if re.match(r'^[=+\-@\t\r]', val_str):
        return f"'{val_str}"
    return val_str
