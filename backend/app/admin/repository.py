"""
Lightweight JSON-file-based metrics and activity repository.
Persists admin metrics, training run logs, operational forecast events,
and system activity logs to disk without any database dependency.

Thread-safe and atomic file-writing practices are enforced.
"""

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import shutil
import tempfile
from threading import RLock
from typing import Any, Dict, List, Optional

logger = logging.getLogger("supply_demand_app.admin_repo")

# Path to backend root
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_DIR = BACKEND_ROOT / "data" / "admin"


class AdminJSONRepository:
    """
    Thread-safe, atomic JSON persistence layer for administrative metrics and activity.
    Strictly avoids database dependencies while preventing corruption via atomic renames.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self._lock = RLock()
        self._metrics_file = self.data_dir / "metrics.json"
        self._training_runs_file = self.data_dir / "training_runs.json"
        self._forecast_events_file = self.data_dir / "forecast_events.json"
        self._activity_file = self.data_dir / "activity.json"

        # Ensure directory and files are initialized safely
        self.init_storage()

    def init_storage(self) -> None:
        """Initializes target directories and JSON files with default zeroed structures."""
        with self._lock:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self._ensure_file(self._metrics_file, self._default_metrics)
            self._ensure_file(self._training_runs_file, list)
            self._ensure_file(self._forecast_events_file, list)
            self._ensure_file(self._activity_file, list)

    def _default_metrics(self) -> Dict[str, Any]:
        """Returns clean initial zero-counter metrics structure."""
        return {
            "total_training_runs": 0,
            "total_evaluated_models": 0,
            "total_forecasts_generated": 0,
            "user_datasets_processed": 0,
            "last_training_time": None,
            "last_evaluation_time": None,
            "last_forecast_time": None,
            "last_upload_time": None,
            "model_statuses": {
                "seasonal_naive": {
                    "name": "Seasonal Naive",
                    "status": "not_evaluated",
                    "last_evaluated": None,
                    "best_wape": None,
                    "best_mae": None,
                    "best_rmse": None,
                },
                "random_forest": {
                    "name": "Random Forest",
                    "status": "not_evaluated",
                    "last_evaluated": None,
                    "best_wape": None,
                    "best_mae": None,
                    "best_rmse": None,
                },
                "xgboost": {
                    "name": "XGBoost",
                    "status": "not_evaluated",
                    "last_evaluated": None,
                    "best_wape": None,
                    "best_mae": None,
                    "best_rmse": None,
                },
            },
            "operational_forecast_metrics": {
                "datasets_processed": 0,
                "forecasts_generated": 0,
                "forecasts_evaluated": 0,
                "mae": None,
                "rmse": None,
                "wape": None,
                "last_forecast_timestamp": None,
            },
        }

    def _ensure_file(self, file_path: Path, default_factory: Any) -> None:
        """Ensures the specified file exists and contains valid JSON."""
        if not file_path.exists() or file_path.stat().st_size == 0:
            initial_data = default_factory() if callable(default_factory) else default_factory
            self._atomic_write(file_path, initial_data)
        else:
            # Validate existing JSON readability
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    json.load(f)
            except Exception as e:
                logger.warning(
                    f"Corrupted admin JSON detected at '{file_path}': {e}. Creating backup and reinitializing."
                )
                backup_path = file_path.with_suffix(f".corrupt_{int(datetime.now(timezone.utc).timestamp())}.bak")
                try:
                    shutil.copy2(file_path, backup_path)
                except Exception:
                    pass
                initial_data = default_factory() if callable(default_factory) else default_factory
                self._atomic_write(file_path, initial_data)

    def _atomic_write(self, file_path: Path, data: Any) -> None:
        """Safely writes JSON data atomically via a temporary file in the same directory."""
        dir_path = file_path.parent
        dir_path.mkdir(parents=True, exist_ok=True)
        # NamedTemporaryFile in same dir ensures atomic rename across filesystem mounts
        with tempfile.NamedTemporaryFile("w", dir=dir_path, delete=False, encoding="utf-8") as tf:
            json.dump(data, tf, indent=2, default=str)
            tf.flush()
            os.fsync(tf.fileno())
            temp_name = tf.name
        os.replace(temp_name, file_path)

    def _safe_read(self, file_path: Path, default_factory: Any) -> Any:
        """Reads JSON data with corrupted file recovery fallback."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading JSON from '{file_path}': {e}. Reinitializing.")
            default_val = default_factory() if callable(default_factory) else default_factory
            self._atomic_write(file_path, default_val)
            return default_val

    # =========================================================================
    # METRICS OPERATIONS
    # =========================================================================

    def get_metrics(self) -> Dict[str, Any]:
        """Retrieves system-wide counters and algorithm status metrics."""
        with self._lock:
            return self._safe_read(self._metrics_file, self._default_metrics)

    def save_metrics(self, metrics: Dict[str, Any]) -> None:
        """Saves updated metric counters atomically."""
        with self._lock:
            self._atomic_write(self._metrics_file, metrics)

    # =========================================================================
    # TRAINING RUNS OPERATIONS
    # =========================================================================

    def get_training_runs(self) -> List[Dict[str, Any]]:
        """Retrieves list of logged training and evaluation runs."""
        with self._lock:
            return self._safe_read(self._training_runs_file, list)

    def append_training_run(self, run: Dict[str, Any]) -> None:
        """Appends a new training run record."""
        with self._lock:
            runs = self._safe_read(self._training_runs_file, list)
            runs.append(run)
            self._atomic_write(self._training_runs_file, runs)

    def update_training_run(self, run_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Updates an existing training run by run_id."""
        with self._lock:
            runs = self._safe_read(self._training_runs_file, list)
            updated_run = None
            for idx, r in enumerate(runs):
                if r.get("run_id") == run_id:
                    runs[idx].update(updates)
                    updated_run = runs[idx]
                    break
            if updated_run:
                self._atomic_write(self._training_runs_file, runs)
            return updated_run

    # =========================================================================
    # FORECAST EVENTS OPERATIONS
    # =========================================================================

    def get_forecast_events(self) -> List[Dict[str, Any]]:
        """Retrieves logged operational forecast events."""
        with self._lock:
            return self._safe_read(self._forecast_events_file, list)

    def append_forecast_event(self, event: Dict[str, Any]) -> None:
        """Appends a new forecast event record."""
        with self._lock:
            events = self._safe_read(self._forecast_events_file, list)
            events.append(event)
            self._atomic_write(self._forecast_events_file, events)

    def update_forecast_event(self, event_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Updates an existing forecast event by event_id."""
        with self._lock:
            events = self._safe_read(self._forecast_events_file, list)
            updated_event = None
            for idx, e in enumerate(events):
                if e.get("event_id") == event_id:
                    events[idx].update(updates)
                    updated_event = events[idx]
                    break
            if updated_event:
                self._atomic_write(self._forecast_events_file, events)
            return updated_event

    # =========================================================================
    # ACTIVITY OPERATIONS
    # =========================================================================

    def get_activities(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent system activity history, sorted chronologically descending."""
        with self._lock:
            acts = self._safe_read(self._activity_file, list)
            # Sort newest first
            sorted_acts = sorted(
                acts,
                key=lambda x: str(x.get("timestamp", "")),
                reverse=True,
            )
            return sorted_acts[:limit]

    def append_activity(self, activity: Dict[str, Any], max_history: int = 200) -> None:
        """Appends an event to the activity stream, maintaining size bound."""
        with self._lock:
            acts = self._safe_read(self._activity_file, list)
            acts.append(activity)
            # Keep bounded history
            if len(acts) > max_history:
                acts = acts[-max_history:]
            self._atomic_write(self._activity_file, acts)

    def reset_all(self) -> None:
        """Resets all metrics and records back to initial zeroed state (for testing)."""
        with self._lock:
            self._atomic_write(self._metrics_file, self._default_metrics())
            self._atomic_write(self._training_runs_file, [])
            self._atomic_write(self._forecast_events_file, [])
            self._atomic_write(self._activity_file, [])


# Global singleton instance pointing to backend/data/admin/
admin_repo = AdminJSONRepository()
