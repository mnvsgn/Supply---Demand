"""
File loader for CSV and XLSX datasets.
Re-exports from app.data_processing.loader.
"""

from app.data_processing.loader import (
    load_dataset_file,
    infer_column_type,
    generate_preview,
    inspect_dataset,
)

__all__ = [
    "load_dataset_file",
    "infer_column_type",
    "generate_preview",
    "inspect_dataset",
]
