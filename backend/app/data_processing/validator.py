import io
import re
import zipfile
from pathlib import Path
from typing import Tuple
from app.core.config import settings
from app.core.errors import (
    FileValidationException,
    PayloadTooLargeException,
    UnsupportedMediaTypeException,
)

# Allowed file extensions
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}

# Signatures to reject immediately for CSV (binary files renamed to .csv)
DISALLOWED_BINARY_SIGNATURES = [
    b"\x7fELF",      # Linux ELF binary
    b"MZ",           # Windows PE executable
    b"PK\x03\x04",   # ZIP / archive
    b"\x1f\x8b",     # GZIP
    b"\x89PNG",      # PNG image
    b"\xff\xd8\xff", # JPEG image
    b"%PDF",         # PDF document
]


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes user filename to prevent path traversal, control characters, and unsafe extensions.
    """
    if not filename:
        return "dataset.csv"

    # Strip directory components (e.g., ../../../etc/passwd -> passwd)
    clean_name = Path(filename).name

    # Remove null bytes, control characters, and path separators
    clean_name = clean_name.replace("\x00", "").replace("/", "").replace("\\", "")

    # Replace suspicious sequences
    clean_name = re.sub(r"\.\.+", ".", clean_name)

    # Normalize whitespace
    clean_name = re.sub(r"\s+", "_", clean_name.strip())

    # Ensure valid length
    if len(clean_name) > 200:
        stem = Path(clean_name).stem[:190]
        ext = Path(clean_name).suffix
        clean_name = f"{stem}{ext}"

    if not clean_name or clean_name.startswith("."):
        clean_name = f"dataset_{clean_name}"

    return clean_name


def validate_file_metadata(filename: str, file_size: int) -> Tuple[str, str]:
    """
    Validates file extension and size constraints.
    Returns (sanitized_filename, extension).
    """
    safe_name = sanitize_filename(filename)
    extension = Path(safe_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise UnsupportedMediaTypeException(
            message=f"Unsupported file format '{extension}'. Only CSV (.csv) and Excel (.xlsx) files are accepted.",
            code="UNSUPPORTED_FILE_FORMAT",
            detail={
                "provided_extension": extension,
                "allowed_extensions": sorted(list(ALLOWED_EXTENSIONS)),
            },
        )

    if file_size <= 0:
        raise FileValidationException(
            message="Uploaded file is empty (0 bytes). Please upload a valid dataset with data.",
            code="EMPTY_FILE",
        )

    if file_size > settings.max_upload_size_bytes:
        raise PayloadTooLargeException(
            message=f"File size ({file_size / (1024 * 1024):.2f} MB) exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB.",
            code="FILE_TOO_LARGE",
            detail={
                "file_size_bytes": file_size,
                "max_allowed_bytes": settings.max_upload_size_bytes,
                "max_allowed_mb": settings.MAX_UPLOAD_SIZE_MB,
            },
        )

    return safe_name, extension


def validate_file_content_signature(content: bytes, extension: str) -> None:
    """
    Verifies actual byte signature to ensure content matches claimed format.
    Does not trust file extension alone.
    """
    if extension == ".xlsx":
        # XLSX must start with ZIP signature (PK\x03\x04 or standard ZIP headers)
        if not (content.startswith(b"PK\x03\x04") or content.startswith(b"PK\x05\x06")):
            raise FileValidationException(
                message="File content does not match a valid Microsoft Excel (.xlsx) workbook.",
                code="INVALID_XLSX_SIGNATURE",
                detail="The file header lacks standard ZIP/OpenXML magic bytes.",
            )

        # Verify that it is a parseable ZIP archive containing Excel workbook components
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                namelist = zf.namelist()
                has_workbook = any(
                    name in namelist for name in ("xl/workbook.xml", "[Content_Types].xml")
                )
                if not has_workbook:
                    raise FileValidationException(
                        message="File is a ZIP archive but does not contain valid Excel (.xlsx) spreadsheet structures.",
                        code="INVALID_EXCEL_STRUCTURE",
                    )
        except zipfile.BadZipFile:
            raise FileValidationException(
                message="Corrupted or malformed XLSX file. Unable to read archive structure.",
                code="CORRUPT_XLSX_FILE",
            )

    elif extension == ".csv":
        # Check for disallowed binary signatures
        for sig in DISALLOWED_BINARY_SIGNATURES:
            if content.startswith(sig):
                raise FileValidationException(
                    message="Binary file detected. Uploaded CSV file must contain plain text tabular data.",
                    code="BINARY_FILE_AS_CSV",
                    detail="File matches a binary executable or archive signature.",
                )

        # Check for null bytes (typical indicator of compiled / binary files)
        if b"\x00" in content[:4096]:
            raise FileValidationException(
                message="File contains binary null bytes and cannot be parsed as text CSV.",
                code="BINARY_CONTENT_IN_CSV",
            )

        # Validate that content can be decoded as text
        decoded = False
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                content[:4096].decode(encoding)
                decoded = True
                break
            except UnicodeDecodeError:
                continue

        if not decoded:
            raise FileValidationException(
                message="Unable to decode CSV file. File must be encoded in UTF-8 or compatible text format.",
                code="CSV_ENCODING_ERROR",
            )
