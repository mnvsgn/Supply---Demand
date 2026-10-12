import csv
import io
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from app.core.config import settings
from app.core.errors import FileValidationException


def infer_column_type(series: pd.Series) -> str:
    """
    Infers user-friendly data type category for a given pandas series.
    Returns: 'datetime' | 'integer' | 'numeric' | 'boolean' | 'categorical' | 'text'
    """
    # Check boolean
    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    # Check numeric
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_float_dtype(series):
        return "numeric"

    # Check datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    # Attempt datetime conversion for object/string columns on non-null sample
    non_null_sample = series.dropna().head(100)
    if not non_null_sample.empty:
        try:
            converted = pd.to_datetime(non_null_sample, errors="coerce", format="mixed")
            valid_dates = converted.notna().sum()
            if valid_dates / len(non_null_sample) >= 0.8:
                return "datetime"
        except Exception:
            pass

    # Attempt numeric conversion for object columns
    if not non_null_sample.empty:
        try:
            converted_num = pd.to_numeric(non_null_sample, errors="coerce")
            if converted_num.notna().sum() / len(non_null_sample) >= 0.9:
                return "numeric"
        except Exception:
            pass

    # Check categorical vs free text
    total_non_null = series.notna().sum()
    if total_non_null > 0:
        unique_count = series.nunique()
        if unique_count <= 25 and (unique_count / total_non_null < 0.5):
            return "categorical"

    return "text"


def sanitize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures column names are strings, stripped of leading/trailing whitespace,
    and disambiguates empty or duplicate names.
    """
    clean_cols = []
    seen = {}

    for idx, col in enumerate(df.columns):
        col_str = str(col).strip()
        if not col_str or col_str.lower().startswith("unnamed:"):
            col_str = f"column_{idx + 1}"

        if col_str in seen:
            seen[col_str] += 1
            col_str = f"{col_str}_{seen[col_str]}"
        else:
            seen[col_str] = 0

        clean_cols.append(col_str)

    df.columns = clean_cols
    return df


def _detect_csv_delimiter(sample_text: str) -> str:
    """
    Sniffs delimiter strictly against valid tabular separators (comma, tab, semicolon, pipe).
    Defaults to comma if no delimiter is detected.
    """
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample_text, delimiters=[",", "\t", ";", "|"])
        return dialect.delimiter
    except Exception:
        return ","


def _parse_csv(content: bytes) -> pd.DataFrame:
    """Parses CSV bytes with encoding and restricted delimiter detection."""
    encodings = ["utf-8", "utf-8-sig", "latin-1"]

    for enc in encodings:
        try:
            sample_text = content[:8192].decode(enc, errors="ignore")
            delimiter = _detect_csv_delimiter(sample_text)

            stream = io.BytesIO(content)
            df = pd.read_csv(stream, encoding=enc, sep=delimiter)
            return df
        except (pd.errors.EmptyDataError, pd.errors.ParserError) as pe:
            raise FileValidationException(
                message=f"Malformed or empty CSV file: {str(pe)}",
                code="MALFORMED_CSV",
            )
        except UnicodeDecodeError:
            continue
        except Exception as e:
            raise FileValidationException(
                message=f"Failed to parse CSV file: {str(e)}",
                code="CSV_PARSE_ERROR",
            )

    raise FileValidationException(
        message="Unable to decode CSV file with supported encodings (UTF-8, Latin-1).",
        code="CSV_ENCODING_FAILURE",
    )


def _parse_xlsx(content: bytes) -> pd.DataFrame:
    """Parses Excel bytes using openpyxl engine."""
    stream = io.BytesIO(content)
    try:
        df = pd.read_excel(stream, engine="openpyxl")
        return df
    except Exception as e:
        raise FileValidationException(
            message=f"Failed to parse Excel (.xlsx) file: {str(e)}",
            code="EXCEL_PARSE_ERROR",
            detail="Ensure the file is a valid, uncorrupted Excel workbook.",
        )


def _build_json_preview(preview_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Converts a DataFrame preview into JSON-compliant dictionaries."""
    records = []
    for _, row in preview_df.iterrows():
        record = {}
        for col, val in row.items():
            if pd.isna(val) or val is None or val is np.nan:
                record[col] = None
            elif isinstance(val, (pd.Timestamp, pd.Period)):
                record[col] = val.isoformat()
            elif isinstance(val, (np.integer, int)):
                record[col] = int(val)
            elif isinstance(val, (np.floating, float)):
                if np.isnan(val) or np.isinf(val):
                    record[col] = None
                else:
                    record[col] = float(val)
            elif isinstance(val, (np.bool_, bool)):
                record[col] = bool(val)
            else:
                record[col] = str(val)
        records.append(record)
    return records


def parse_and_validate_dataset(
    content: bytes, extension: str
) -> Tuple[pd.DataFrame, Dict[str, str], List[Dict[str, Any]]]:
    """
    Parses raw bytes into a pandas DataFrame using appropriate engines.
    Validates row and column constraints, infers dtypes, and builds a preview.

    Returns: (df, dtypes_dict, preview_records)
    """
    df: pd.DataFrame

    if extension == ".csv":
        df = _parse_csv(content)
    elif extension == ".xlsx":
        df = _parse_xlsx(content)
    else:
        raise FileValidationException(
            message=f"Unsupported format {extension}", code="UNSUPPORTED_FORMAT"
        )

    # Sanitize column headers
    df = sanitize_dataframe_columns(df)

    # Validate row constraints
    row_count = len(df)
    if row_count < settings.MIN_ROWS:
        raise FileValidationException(
            message=f"Dataset must contain at least {settings.MIN_ROWS} row of data (found 0).",
            code="EMPTY_DATASET_ROWS",
            detail="The uploaded file contains headers or comments but no data records.",
        )

    if row_count > settings.MAX_ROWS:
        raise FileValidationException(
            message=f"Dataset row count ({row_count:,}) exceeds maximum allowed limit of {settings.MAX_ROWS:,}.",
            code="TOO_MANY_ROWS",
            detail={"rows": row_count, "max_allowed": settings.MAX_ROWS},
        )

    # Validate column constraints
    col_count = len(df.columns)
    if col_count < settings.MIN_COLS:
        raise FileValidationException(
            message=f"Dataset must contain at least {settings.MIN_COLS} columns (found {col_count}). "
            "A minimum of a timestamp/date column and a demand target is required.",
            code="INSUFFICIENT_COLUMNS",
            detail={"columns_found": list(df.columns)},
        )

    if col_count > settings.MAX_COLS:
        raise FileValidationException(
            message=f"Dataset column count ({col_count}) exceeds maximum allowed limit of {settings.MAX_COLS}.",
            code="TOO_MANY_COLUMNS",
            detail={"columns_count": col_count, "max_allowed": settings.MAX_COLS},
        )

    # Infer column data types
    dtypes = {col: infer_column_type(df[col]) for col in df.columns}

    # Generate limited preview (first PREVIEW_ROWS rows)
    preview_df = df.head(settings.PREVIEW_ROWS).copy()

    # Normalize NaN, NaT, Inf to None for valid JSON serialization
    preview_records = _build_json_preview(preview_df)

    return df, dtypes, preview_records