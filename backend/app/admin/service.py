"""
Admin Service module for metric tracking, activity logging,
operational forecast verification, and system telemetry.
"""

from datetime import datetime, timezone
import platform
import secrets
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import sklearn
import xgboost
import fastapi

from app.admin.repository import AdminJSONRepository, admin_repo
from app.core.config import settings
from app.evaluation.metrics import calculate_mae, calculate_rmse, calculate_wape


class AdminService:
    """
    Coordinates administration metrics, performance aggregation,
    and runtime system telemetry without any database dependency.
    """

    def __init__(self, repo: Optional[AdminJSONRepository] = None):
        self.repo = repo or admin_repo

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # =========================================================================
    # WORKFLOW INTEGRATION HOOKS
    # =========================================================================

    def record_training_started(
        self,
        model_type: str,
        dataset_id: Optional[str] = None,
        horizon: int = 14,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Invoked when model training begins."""
        run_id = f"run_{secrets.token_hex(8)}"
        now = self._now_iso()

        run_record = {
            "run_id": run_id,
            "model_type": model_type,
            "dataset_id": dataset_id or "unknown",
            "status": "started",
            "start_time": now,
            "end_time": None,
            "duration_seconds": None,
            "horizon": horizon,
            "parameters": parameters or {},
            "metrics": None,
            "error": None,
        }
        self.repo.append_training_run(run_record)

        self.repo.append_activity({
            "activity_id": f"act_{secrets.token_hex(6)}",
            "type": "training",
            "title": "Model Training Started",
            "description": f"Training {model_type.replace('_', ' ').title()} for horizon {horizon}",
            "timestamp": now,
            "status": "in_progress",
            "metadata": {"run_id": run_id, "model_type": model_type, "dataset_id": dataset_id},
        })

        return run_id

    def record_training_completed(
        self,
        run_id: str,
        model_type: str,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Invoked when model training successfully completes."""
        now = self._now_iso()

        # Find run start time to compute duration
        runs = self.repo.get_training_runs()
        target_run = next((r for r in runs if r.get("run_id") == run_id), None)
        duration_sec = 0.0
        if target_run and target_run.get("start_time"):
            try:
                start_dt = datetime.fromisoformat(target_run["start_time"])
                duration_sec = round((datetime.now(timezone.utc) - start_dt).total_seconds(), 2)
            except Exception:
                duration_sec = 0.0

        self.repo.update_training_run(
            run_id=run_id,
            updates={
                "status": "completed",
                "end_time": now,
                "duration_seconds": duration_sec,
                "metrics": metrics,
            },
        )

        # Update global metrics counters
        m = self.repo.get_metrics()
        m["total_training_runs"] = m.get("total_training_runs", 0) + 1
        m["last_training_time"] = now

        # Update model status
        canonical_key = "seasonal_naive" if "naive" in model_type else model_type.lower()
        if canonical_key in m.get("model_statuses", {}):
            status_entry = m["model_statuses"][canonical_key]
            status_entry["status"] = "trained"
            status_entry["last_evaluated"] = now
            if metrics:
                if metrics.get("wape") is not None:
                    status_entry["best_wape"] = metrics.get("wape")
                if metrics.get("mae") is not None:
                    status_entry["best_mae"] = metrics.get("mae")
                if metrics.get("rmse") is not None:
                    status_entry["best_rmse"] = metrics.get("rmse")

        self.repo.save_metrics(m)

        self.repo.append_activity({
            "activity_id": f"act_{secrets.token_hex(6)}",
            "type": "training",
            "title": "Model Training Completed",
            "description": f"Successfully fit {model_type.replace('_', ' ').title()} in {duration_sec}s",
            "timestamp": now,
            "status": "success",
            "metadata": {"run_id": run_id, "duration_seconds": duration_sec, "metrics": metrics},
        })

    def record_training_failed(self, run_id: str, error: str) -> None:
        """Invoked when model training fails."""
        now = self._now_iso()
        self.repo.update_training_run(
            run_id=run_id,
            updates={
                "status": "failed",
                "end_time": now,
                "error": error,
            },
        )

        self.repo.append_activity({
            "activity_id": f"act_{secrets.token_hex(6)}",
            "type": "training",
            "title": "Model Training Failed",
            "description": f"Training failed: {error[:120]}",
            "timestamp": now,
            "status": "failed",
            "metadata": {"run_id": run_id, "error": error},
        })

    def record_evaluation_completed(
        self,
        dataset_id: Optional[str] = None,
        horizon: int = 14,
        primary_metric: str = "wape",
        candidate_models: Optional[List[str]] = None,
        comparison_table: Optional[List[Dict[str, Any]]] = None,
        winning_model: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Invoked when model evaluation and comparative backtesting completes."""
        now = self._now_iso()
        candidates = candidate_models or ["Seasonal Naive", "Random Forest", "XGBoost"]

        m = self.repo.get_metrics()
        m["total_evaluated_models"] = m.get("total_evaluated_models", 0) + len(candidates)
        m["last_evaluation_time"] = now

        # Update candidate status in metrics
        if comparison_table:
            for row in comparison_table:
                model_name = str(row.get("model_name", "")).lower()
                key = "seasonal_naive" if "naive" in model_name else ("random_forest" if "forest" in model_name else ("xgboost" if "xgboost" in model_name else None))
                if key and key in m.get("model_statuses", {}):
                    entry = m["model_statuses"][key]
                    entry["status"] = "evaluated"
                    entry["last_evaluated"] = now
                    row_metrics = row.get("metrics") or {}
                    if row_metrics.get("wape") is not None:
                        entry["best_wape"] = row_metrics["wape"]
                    if row_metrics.get("mae") is not None:
                        entry["best_mae"] = row_metrics["mae"]
                    if row_metrics.get("rmse") is not None:
                        entry["best_rmse"] = row_metrics["rmse"]

        self.repo.save_metrics(m)

        self.repo.append_activity({
            "activity_id": f"act_{secrets.token_hex(6)}",
            "type": "evaluation",
            "title": "Comparative Evaluation Completed",
            "description": f"Evaluated {len(candidates)} candidates. Best model: {winning_model or 'Auto-Selected'}",
            "timestamp": now,
            "status": "success",
            "metadata": {
                "dataset_id": dataset_id,
                "winning_model": winning_model,
                "primary_metric": primary_metric,
            },
        })

    def record_dataset_processed(
        self,
        dataset_id: str,
        filename: str,
        row_count: int,
        column_count: int,
    ) -> None:
        """Invoked when a user dataset is ingested and registered."""
        now = self._now_iso()

        m = self.repo.get_metrics()
        m["user_datasets_processed"] = m.get("user_datasets_processed", 0) + 1
        m["last_upload_time"] = now
        op = m.get("operational_forecast_metrics", {})
        op["datasets_processed"] = op.get("datasets_processed", 0) + 1
        m["operational_forecast_metrics"] = op
        self.repo.save_metrics(m)

        self.repo.append_activity({
            "activity_id": f"act_{secrets.token_hex(6)}",
            "type": "upload",
            "title": "Dataset Ingested",
            "description": f"Processed '{filename}' with {row_count:,} records",
            "timestamp": now,
            "status": "success",
            "metadata": {"dataset_id": dataset_id, "filename": filename, "row_count": row_count, "column_count": column_count},
        })

    def record_forecast_generated(
        self,
        dataset_id: Optional[str] = None,
        session_id: Optional[str] = None,
        model_name: str = "Forecast Model",
        horizon: int = 14,
        target_level: str = "aggregate",
        product_id: Optional[str] = None,
        points_count: int = 14,
        forecast_points: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Invoked when a multi-step forecast is generated."""
        now = self._now_iso()
        event_id = f"fc_{secrets.token_hex(8)}"

        # 1. Update counters
        m = self.repo.get_metrics()
        m["total_forecasts_generated"] = m.get("total_forecasts_generated", 0) + 1
        m["last_forecast_time"] = now
        op = m.get("operational_forecast_metrics", {})
        op["forecasts_generated"] = op.get("forecasts_generated", 0) + 1
        op["last_forecast_timestamp"] = now
        m["operational_forecast_metrics"] = op
        self.repo.save_metrics(m)

        # 2. Append event
        event_record = {
            "event_id": event_id,
            "dataset_id": dataset_id or "unknown",
            "session_id": session_id or "default",
            "model_name": model_name,
            "horizon": horizon,
            "target_level": target_level,
            "product_id": product_id,
            "points_count": points_count,
            "forecast_points": forecast_points or [],
            "created_at": now,
            "evaluated_against_actual": False,
            "actual_metrics": None,
        }
        self.repo.append_forecast_event(event_record)

        # 3. Log activity
        self.repo.append_activity({
            "activity_id": f"act_{secrets.token_hex(6)}",
            "type": "forecast",
            "title": "Forecast Generated",
            "description": f"Generated {horizon}-period projection using {model_name}",
            "timestamp": now,
            "status": "success",
            "metadata": {
                "event_id": event_id,
                "dataset_id": dataset_id,
                "model_name": model_name,
                "horizon": horizon,
            },
        })

        return event_id

    def verify_forecast_operational(
        self,
        event_id: str,
        actual_observations: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates previously generated forecast points against actual observations.
        Strictly calculates operational metrics only when genuine observations exist.
        """
        events = self.repo.get_forecast_events()
        event = next((e for e in events if e.get("event_id") == event_id), None)
        if not event or not event.get("forecast_points"):
            return None

        # Build mapping of date -> actual demand
        actuals_by_date = {}
        for obs in actual_observations:
            d = str(obs.get("date", "")).split("T")[0]
            val = obs.get("demand") if "demand" in obs else obs.get("actual")
            if d and val is not None:
                try:
                    actuals_by_date[d] = float(val)
                except (ValueError, TypeError):
                    pass

        y_true = []
        y_pred = []
        for pt in event["forecast_points"]:
            d = str(pt.get("date", "")).split("T")[0]
            if d in actuals_by_date:
                pred_val = pt.get("predicted_demand") if "predicted_demand" in pt else pt.get("forecast")
                if pred_val is not None:
                    y_true.append(actuals_by_date[d])
                    y_pred.append(float(pred_val))

        if len(y_true) < 1:
            return None

        arr_true = np.array(y_true)
        arr_pred = np.array(y_pred)

        mae = float(calculate_mae(arr_true, arr_pred))
        rmse = float(calculate_rmse(arr_true, arr_pred))
        wape = float(calculate_wape(arr_true, arr_pred))

        metrics = {
            "mae": round(mae, 3),
            "rmse": round(rmse, 3),
            "wape": round(wape, 4),
            "matched_periods": len(y_true),
        }

        # Update event record
        self.repo.update_forecast_event(
            event_id=event_id,
            updates={
                "evaluated_against_actual": True,
                "actual_metrics": metrics,
            },
        )

        # Update global operational metrics
        now = self._now_iso()
        m = self.repo.get_metrics()
        op = m.get("operational_forecast_metrics", {})
        op["forecasts_evaluated"] = op.get("forecasts_evaluated", 0) + 1
        op["mae"] = metrics["mae"]
        op["rmse"] = metrics["rmse"]
        op["wape"] = metrics["wape"]
        m["operational_forecast_metrics"] = op
        self.repo.save_metrics(m)

        self.repo.append_activity({
            "activity_id": f"act_{secrets.token_hex(6)}",
            "type": "verification",
            "title": "Operational Forecast Evaluated",
            "description": f"Verified forecast against {len(y_true)} actual observations (WAPE: {round(wape*100, 1)}%)",
            "timestamp": now,
            "status": "success",
            "metadata": {"event_id": event_id, "metrics": metrics},
        })

        return metrics

    # =========================================================================
    # DASHBOARD & PERFORMANCE DATA AGGREGATORS
    # =========================================================================

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Provides high-level dashboard counters, model status, and recent activity."""
        m = self.repo.get_metrics()
        recent_activity = self.repo.get_activities(limit=15)

        # Clean model status dictionary
        model_statuses = []
        raw_statuses = m.get("model_statuses", {})
        for key, info in raw_statuses.items():
            model_statuses.append({
                "key": key,
                "name": info.get("name", key.title()),
                "status": info.get("status", "not_evaluated"),
                "last_evaluated": info.get("last_evaluated"),
                "best_wape": info.get("best_wape"),
                "best_mae": info.get("best_mae"),
                "best_rmse": info.get("best_rmse"),
            })

        return {
            "total_training_runs": m.get("total_training_runs", 0),
            "total_evaluated_models": m.get("total_evaluated_models", 0),
            "total_forecasts_generated": m.get("total_forecasts_generated", 0),
            "user_datasets_processed": m.get("user_datasets_processed", 0),
            "timestamps": {
                "last_training_time": m.get("last_training_time"),
                "last_evaluation_time": m.get("last_evaluation_time"),
                "last_forecast_time": m.get("last_forecast_time"),
                "last_upload_time": m.get("last_upload_time"),
            },
            "model_statuses": model_statuses,
            "recent_activity": recent_activity,
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Provides detailed model performance divided into 3 distinct sections:
        A. Training & Testing Performance
        B. Operational Forecast Performance
        C. Model Comparison
        """
        m = self.repo.get_metrics()
        runs = self.repo.get_training_runs()
        raw_statuses = m.get("model_statuses", {})

        # -------------------------------------------------------------
        # Section A: Training & Testing Performance
        # -------------------------------------------------------------
        training_runs_count = m.get("total_training_runs", 0)
        evaluated_models_count = m.get("total_evaluated_models", 0)
        last_eval_time = m.get("last_evaluation_time")

        # Find best-performing model across evaluated algorithms (lowest WAPE)
        best_model_name = None
        min_wape = float("inf")
        candidate_performances = []

        for key in ["seasonal_naive", "random_forest", "xgboost"]:
            st = raw_statuses.get(key, {})
            name = st.get("name", key.title())
            status = st.get("status", "not_evaluated")
            wape = st.get("best_wape")
            mae = st.get("best_mae")
            rmse = st.get("best_rmse")

            if status in ("trained", "evaluated") and wape is not None:
                if wape < min_wape:
                    min_wape = wape
                    best_model_name = name

            candidate_performances.append({
                "key": key,
                "name": name,
                "status": status,
                "last_evaluated": st.get("last_evaluated"),
                "mae": mae,
                "rmse": rmse,
                "wape": wape,
            })

        section_a = {
            "training_runs_count": training_runs_count,
            "evaluated_series_count": evaluated_models_count,
            "best_performing_model": best_model_name if best_model_name else "Not evaluated",
            "last_evaluation_time": last_eval_time,
            "candidate_models": candidate_performances,
            "has_evaluations": evaluated_models_count > 0 or training_runs_count > 0,
        }

        # -------------------------------------------------------------
        # Section B: Operational Forecast Performance
        # -------------------------------------------------------------
        op_metrics = m.get("operational_forecast_metrics", {})
        section_b = {
            "datasets_processed": op_metrics.get("datasets_processed", 0),
            "forecasts_generated": op_metrics.get("forecasts_generated", 0),
            "forecasts_evaluated": op_metrics.get("forecasts_evaluated", 0),
            "mae": op_metrics.get("mae"),
            "rmse": op_metrics.get("rmse"),
            "wape": op_metrics.get("wape"),
            "last_forecast_timestamp": op_metrics.get("last_forecast_timestamp"),
            "has_operational_evaluations": (op_metrics.get("forecasts_evaluated", 0) > 0),
        }

        # -------------------------------------------------------------
        # Section C: Model Comparison (Chart & Comparison Table)
        # -------------------------------------------------------------
        comparison_rows = []
        has_comparison_data = False
        for c in candidate_performances:
            if c["wape"] is not None:
                has_comparison_data = True
                comparison_rows.append({
                    "model_name": c["name"],
                    "wape_pct": round(c["wape"] * 100, 1) if c["wape"] <= 1.0 else round(c["wape"], 1),
                    "mae": c["mae"],
                    "rmse": c["rmse"],
                    "status": "Eligible" if c["status"] == "evaluated" else "Trained",
                })

        section_c = {
            "has_data": has_comparison_data,
            "comparison_table": comparison_rows,
        }

        return {
            "training_and_testing": section_a,
            "operational_forecasts": section_b,
            "model_comparison": section_c,
        }

    def get_system_info(self) -> Dict[str, Any]:
        """Provides genuine backend telemetry and library versions without exposing secrets."""
        m = self.repo.get_metrics()

        return {
            "application": {
                "name": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG,
                "backend_status": "healthy",
                "frontend_status": "connected",
            },
            "environment_info": {
                "os": platform.system(),
                "os_release": platform.release(),
                "python_version": platform.python_version(),
            },
            "library_versions": {
                "fastapi": fastapi.__version__,
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "scikit_learn": sklearn.__version__,
                "xgboost": xgboost.__version__,
            },
            "supported_capabilities": {
                "models": ["Seasonal Naive", "Random Forest Regressor", "XGBoost Regressor", "Auto-Selection"],
                "file_formats": [".csv", ".xlsx"],
                "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
                "supported_frequencies": ["Daily (D)", "Weekly (W)", "Monthly (M)"],
            },
            "session_configuration": {
                "session_expiry_minutes": settings.SESSION_EXPIRY_MINUTES,
                "session_idle_timeout_minutes": settings.SESSION_IDLE_TIMEOUT_MINUTES,
                "session_cleanup_interval_minutes": settings.SESSION_CLEANUP_INTERVAL_MINUTES,
            },
            "activity_timestamps": {
                "last_successful_training": m.get("last_training_time"),
                "last_successful_evaluation": m.get("last_evaluation_time"),
                "last_successful_forecast": m.get("last_forecast_time"),
                "last_dataset_upload": m.get("last_upload_time"),
            },
            "system_time_utc": self._now_iso(),
        }


# Global service singleton
admin_service = AdminService()
