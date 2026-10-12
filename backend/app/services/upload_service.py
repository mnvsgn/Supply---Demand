"""
Upload service module.
Handles dataset file validation, content signature inspection,
parsing, schema detection, and registration into session-isolated storage.
"""

from typing import Optional, Tuple
from app.data_processing.loader import parse_and_validate_dataset
from app.data_processing.schema_detector import schema_detector
from app.data_processing.validator import (
    validate_file_content_signature,
    validate_file_metadata,
)
from app.schemas.dataset import DatasetUploadResponse
from app.services.dataset_registry import dataset_registry


class UploadService:
    """Service handling file upload pipeline and session isolation."""

    def process_upload(
        self,
        raw_filename: str,
        content: bytes,
        session_id: Optional[str] = None,
    ) -> Tuple[DatasetUploadResponse, str]:
        """
        Validates, parses, detects schema, and registers uploaded dataset.
        Returns (DatasetUploadResponse, active_session_id).
        """
        # 1. Metadata and bounds validation
        safe_filename, extension = validate_file_metadata(
            filename=raw_filename or "uploaded_dataset",
            file_size=len(content),
        )

        # 2. Magic byte file signature validation
        validate_file_content_signature(content=content, extension=extension)

        # 3. Parse tabular structure and build preview
        df, dtypes, preview = parse_and_validate_dataset(
            content=content, extension=extension
        )

        # 4. Schema detection and ambiguity analysis
        detection = schema_detector.detect(df, dtypes)

        # 5. Session-isolated dataset registration
        record = dataset_registry.register_dataset(
            original_filename=safe_filename,
            extension=extension,
            content=content,
            row_count=len(df),
            columns=list(df.columns),
            dtypes=dtypes,
            preview=preview,
            raw_df=df,
            suggested_mapping=detection.suggested_mapping,
            mapping_confidence=detection.confidence,
            ambiguity_warnings=detection.ambiguity_warnings,
            requires_confirmation=detection.requires_confirmation,
            session_id=session_id,
        )

        active_sid = record.session_id or ""

        response_obj = DatasetUploadResponse(
            dataset_id=record.dataset_id,
            filename=record.original_filename,
            file_type=record.file_type,
            file_size_bytes=record.file_size_bytes,
            row_count=record.row_count,
            column_count=record.column_count,
            columns=record.columns,
            dtypes=record.dtypes,
            preview=record.preview,
            preview_rows_count=len(record.preview),
            suggested_mapping=record.suggested_mapping,
            mapping_confidence=record.mapping_confidence,
            ambiguity_warnings=record.ambiguity_warnings,
            requires_confirmation=record.requires_confirmation,
            created_at=record.created_at,
            expires_at=record.expires_at,
            session_id=active_sid,
        )

        return response_obj, active_sid


upload_service = UploadService()
