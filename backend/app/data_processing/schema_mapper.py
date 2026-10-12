from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from app.core.errors import ValidationException


CANONICAL_REQUIRED_FIELDS = ["date", "demand"]
CANONICAL_OPTIONAL_FIELDS = ["product_id", "store_id", "price", "promotion"]
ALL_CANONICAL_FIELDS = CANONICAL_REQUIRED_FIELDS + CANONICAL_OPTIONAL_FIELDS


class SchemaMapper:
    """
    Validates and applies column mapping from raw dataset columns to canonical internal fields:
    date, demand, product_id, store_id, price, promotion.
    """

    def validate_mapping(
        self,
        available_columns: List[str],
        mapping: Dict[str, Optional[str]],
    ) -> None:
        """
        Validates mapping definitions:
        - Required fields (date, demand) must be present.
        - Mapped columns must exist in available_columns.
        - Disallows duplicate mapping of the same raw column to multiple canonical fields.
        """
        # 1. Required fields
        for req in CANONICAL_REQUIRED_FIELDS:
            target_col = mapping.get(req)
            if not target_col:
                raise ValidationException(
                    message=f"Missing required mapping for canonical field '{req}'.",
                    code="MISSING_REQUIRED_MAPPING",
                    detail={"field": req, "available_columns": available_columns},
                )
            if target_col not in available_columns:
                raise ValidationException(
                    message=f"Mapped column '{target_col}' for '{req}' does not exist in dataset.",
                    code="COLUMN_NOT_FOUND",
                    detail={"field": req, "column": target_col, "available_columns": available_columns},
                )

        # 2. Optional fields
        for opt in CANONICAL_OPTIONAL_FIELDS:
            target_col = mapping.get(opt)
            if target_col:
                if target_col not in available_columns:
                    raise ValidationException(
                        message=f"Mapped column '{target_col}' for optional field '{opt}' does not exist in dataset.",
                        code="COLUMN_NOT_FOUND",
                        detail={"field": opt, "column": target_col, "available_columns": available_columns},
                    )

        # 3. Disallow mapping the same raw column to multiple canonical fields
        mapped_raw_cols: Dict[str, str] = {}
        for role, col in mapping.items():
            if col:
                if col in mapped_raw_cols:
                    prev_role = mapped_raw_cols[col]
                    raise ValidationException(
                        message=f"Raw column '{col}' cannot be mapped to both '{prev_role}' and '{role}'.",
                        code="DUPLICATE_COLUMN_MAPPING",
                        detail={"column": col, "roles": [prev_role, role]},
                    )
                mapped_raw_cols[col] = role

    def apply_mapping(
        self,
        df: pd.DataFrame,
        mapping: Dict[str, Optional[str]],
    ) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """
        Creates a mapped canonical DataFrame.
        Returns: (mapped_df, active_canonical_mapping)
        """
        self.validate_mapping(list(df.columns), mapping)

        rename_dict = {}
        active_mapping: Dict[str, str] = {}

        for role in ALL_CANONICAL_FIELDS:
            col_name = mapping.get(role)
            if col_name and col_name in df.columns:
                rename_dict[col_name] = role
                active_mapping[role] = col_name

        # Select mapped columns, renaming to canonical names
        mapped_df = df[list(rename_dict.keys())].rename(columns=rename_dict).copy()
        return mapped_df, active_mapping


# Global singleton
schema_mapper = SchemaMapper()
