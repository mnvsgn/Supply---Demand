import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from app.core.config import settings
from app.core.logging import logger


@dataclass
class DatasetRecord:
    dataset_id: str
    original_filename: str
    storage_path: Path
    file_type: str
    file_size_bytes: int
    row_count: int
    column_count: int
    columns: List[str]
    dtypes: Dict[str, str]
    preview: List[Dict[str, Any]]
    created_at: datetime
    expires_at: datetime
    # In-memory DataFrame caches and normalization state
    raw_df: Optional[pd.DataFrame] = None
    normalized_df: Optional[pd.DataFrame] = None
    suggested_mapping: Optional[Dict[str, Optional[str]]] = None
    mapping_confidence: Optional[Dict[str, str]] = None
    ambiguity_warnings: List[str] = field(default_factory=list)
    requires_confirmation: bool = False
    active_mapping: Optional[Dict[str, Optional[str]]] = None
    data_quality: Optional[Dict[str, Any]] = None
    normalization_summary: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class DatasetRegistry:
    """
    In-memory registry managing temporary uploaded datasets and their files on disk.
    Provides session tracking, path-traversal isolation, and automatic TTL expiration.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir or settings.STORAGE_DIR).resolve()
        self._ensure_storage_dir()
        self._records: Dict[str, DatasetRecord] = {}

    def _ensure_storage_dir(self) -> None:
        """Ensures that the dataset storage directory exists outside public frontend."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def cleanup_expired(self) -> int:
        """Purges expired datasets from memory and deletes their storage files."""
        now = datetime.now(timezone.utc)
        expired_ids = [
            did for did, record in self._records.items() if now > record.expires_at
        ]

        cleaned = 0
        for did in expired_ids:
            record = self._records.pop(did, None)
            if record and record.storage_path.exists():
                try:
                    record.storage_path.unlink()
                    cleaned += 1
                except Exception as e:
                    logger.error(f"Failed to delete expired file {record.storage_path}: {e}")

        if cleaned > 0:
            logger.info(f"Purged {cleaned} expired dataset(s) from temporary registry.")
        return cleaned

    def delete_dataset(self, dataset_id: str) -> bool:
        """Removes a dataset from the registry and deletes its disk file."""
        record = self._records.pop(dataset_id, None)
        if not record:
            return False
        if record.storage_path.exists():
            try:
                record.storage_path.unlink()
            except Exception as e:
                logger.error(f"Failed to delete dataset file {record.storage_path}: {e}")
        return True

    def register_dataset(
        self,
        original_filename: str,
        extension: str,
        content: bytes,
        row_count: int,
        columns: List[str],
        dtypes: Dict[str, str],
        preview: List[Dict[str, Any]],
        raw_df: Optional[pd.DataFrame] = None,
        suggested_mapping: Optional[Dict[str, Optional[str]]] = None,
        mapping_confidence: Optional[Dict[str, str]] = None,
        ambiguity_warnings: Optional[List[str]] = None,
        requires_confirmation: bool = False,
        session_id: Optional[str] = None,
    ) -> DatasetRecord:
        """
        Stores file content under an isolated randomized identifier and records metadata.
        Associates dataset with an unguessable session.
        """
        from app.services.session_manager import session_manager

        self.cleanup_expired()

        # Resolve or auto-create session
        target_session = None
        if session_id:
            target_session = session_manager.get_session(session_id, touch=True)
            if not target_session:
                # If passed session expired or missing, initialize a fresh unguessable session
                target_session = session_manager.create_session()
                session_id = target_session.session_id
        else:
            target_session = session_manager.create_session()
            session_id = target_session.session_id

        dataset_id = str(uuid.uuid4())
        random_slug = uuid.uuid4().hex[:12]
        internal_filename = f"dataset_{dataset_id}_{random_slug}{extension}"

        # Place files in isolated session directory
        target_dir = target_session.storage_dir / "datasets"
        target_dir.mkdir(parents=True, exist_ok=True)
        storage_path = (target_dir / internal_filename).resolve()

        # Prevent path traversal
        if not str(storage_path).startswith(str(target_session.storage_dir)):
            raise ValueError("Path traversal attempt detected during dataset storage.")

        # Save to disk outside frontend
        with open(storage_path, "wb") as f:
            f.write(content)

        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(minutes=settings.SESSION_EXPIRY_MINUTES)

        record = DatasetRecord(
            dataset_id=dataset_id,
            original_filename=original_filename,
            storage_path=storage_path,
            file_type=extension.lstrip(".").lower(),
            file_size_bytes=len(content),
            row_count=row_count,
            column_count=len(columns),
            columns=columns,
            dtypes=dtypes,
            preview=preview,
            created_at=created_at,
            expires_at=expires_at,
            raw_df=raw_df,
            suggested_mapping=suggested_mapping,
            mapping_confidence=mapping_confidence,
            ambiguity_warnings=ambiguity_warnings or [],
            requires_confirmation=requires_confirmation,
            session_id=session_id,
        )

        self._records[dataset_id] = record
        # Register dataset in session
        session_manager.attach_dataset(session_id, dataset_id)

        logger.info(
            f"Registered dataset {dataset_id} for session {session_id[:12]}*** "
            f"({original_filename}, {row_count} rows, {len(columns)} cols)"
        )
        return record


    def get(self, dataset_id: str) -> Optional[DatasetRecord]:
        """Retrieves an active dataset record if not expired."""
        self.cleanup_expired()
        record = self._records.get(dataset_id)
        if not record:
            return None

        if datetime.now(timezone.utc) > record.expires_at:
            self._records.pop(dataset_id, None)
            if record.storage_path.exists():
                try:
                    record.storage_path.unlink()
                except Exception:
                    pass
            return None

        return record

    def get_for_session(self, session_id: str, dataset_id: str) -> Optional[DatasetRecord]:
        """
        Retrieves a dataset record strictly verifying session ownership.
        Raises NotFoundException if dataset does not belong to session.
        """
        from app.services.session_manager import session_manager
        session_manager.verify_dataset_ownership(session_id, dataset_id)
        return self.get(dataset_id)

    def get_raw_dataframe(self, dataset_id: str) -> pd.DataFrame:
        """
        Retrieves the raw source DataFrame from memory cache or reloads from storage.
        """
        record = self.get(dataset_id)
        if not record:
            raise KeyError(f"Dataset session '{dataset_id}' not found or expired.")

        if record.raw_df is not None:
            return record.raw_df.copy()

        # Reload from disk if cleared from cache
        if record.file_type == "csv":
            df = pd.read_csv(record.storage_path)
        elif record.file_type == "xlsx":
            df = pd.read_excel(record.storage_path, engine="openpyxl")
        else:
            raise ValueError(f"Unknown format {record.file_type}")

        record.raw_df = df
        return df.copy()

    def update_mapping(
        self,
        dataset_id: str,
        active_mapping: Dict[str, Optional[str]],
        normalized_df: pd.DataFrame,
        data_quality: Dict[str, Any],
        normalization_summary: Dict[str, Any],
    ) -> DatasetRecord:
        """
        Saves user-confirmed canonical mapping and attaches normalized representation.
        """
        record = self.get(dataset_id)
        if not record:
            raise KeyError(f"Dataset session '{dataset_id}' not found or expired.")

        record.active_mapping = active_mapping
        record.normalized_df = normalized_df
        record.data_quality = data_quality
        record.normalization_summary = normalization_summary

        logger.info(f"Updated schema mapping for dataset {dataset_id}: {active_mapping}")
        return record

    def clear(self) -> None:
        """Clears all records and removes temporary files (useful for test resets)."""
        from app.services.session_manager import session_manager
        for record in self._records.values():
            if record.storage_path.exists():
                try:
                    record.storage_path.unlink()
                except Exception:
                    pass
        self._records.clear()
        session_manager.clear_all()


# Global registry instance
dataset_registry = DatasetRegistry()
