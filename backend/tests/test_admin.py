"""
Unit and integration tests for Admin JSON persistence, metrics tracking,
operational forecast verification, telemetry, and administrator authentication.
"""

import json
from pathlib import Path
import tempfile
import threading
import pytest
from starlette.testclient import TestClient

from app.admin.auth import authenticate_admin, revoke_admin_token, validate_admin_token
from app.admin.repository import AdminJSONRepository
from app.admin.service import AdminService
from app.core.config import settings
from app.main import app


@pytest.fixture
def temp_admin_repo(tmp_path):
    """Provides an isolated AdminJSONRepository in a temporary directory."""
    repo = AdminJSONRepository(data_dir=tmp_path / "admin_test")
    return repo


@pytest.fixture
def temp_admin_service(temp_admin_repo):
    """Provides an isolated AdminService backed by a temporary repo."""
    return AdminService(repo=temp_admin_repo)


def test_admin_repository_initialization_empty_state(temp_admin_repo):
    """Verify that files are created automatically with zero counters and empty collections."""
    metrics = temp_admin_repo.get_metrics()
    assert metrics["total_training_runs"] == 0
    assert metrics["total_evaluated_models"] == 0
    assert metrics["total_forecasts_generated"] == 0
    assert metrics["user_datasets_processed"] == 0
    assert metrics["model_statuses"]["seasonal_naive"]["status"] == "not_evaluated"
    assert metrics["model_statuses"]["random_forest"]["status"] == "not_evaluated"
    assert metrics["model_statuses"]["xgboost"]["status"] == "not_evaluated"

    runs = temp_admin_repo.get_training_runs()
    assert runs == []

    events = temp_admin_repo.get_forecast_events()
    assert events == []

    activities = temp_admin_repo.get_activities()
    assert activities == []


def test_admin_repository_corrupted_file_recovery(tmp_path):
    """Verify that a corrupted JSON file is safely recovered without crashing."""
    admin_dir = tmp_path / "corrupt_test"
    admin_dir.mkdir(parents=True)
    bad_file = admin_dir / "metrics.json"
    bad_file.write_text("{this is corrupted invalid json content!!!", encoding="utf-8")

    # Initialization should detect corrupted file, backup, and restore defaults
    repo = AdminJSONRepository(data_dir=admin_dir)
    recovered_metrics = repo.get_metrics()
    assert recovered_metrics["total_training_runs"] == 0

    # Ensure backup was created
    bak_files = list(admin_dir.glob("metrics.corrupt_*.bak"))
    assert len(bak_files) >= 1


def test_admin_repository_concurrent_thread_safety(temp_admin_repo):
    """Verify that concurrent writes across multiple threads do not corrupt JSON files."""
    num_threads = 20
    runs_per_thread = 5

    def worker(worker_id):
        for i in range(runs_per_thread):
            temp_admin_repo.append_activity({
                "activity_id": f"act_{worker_id}_{i}",
                "title": f"Activity {worker_id}-{i}",
                "timestamp": f"2026-10-10T12:00:{worker_id:02d}.{i:03d}Z",
            })

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    activities = temp_admin_repo.get_activities(limit=200)
    assert len(activities) == num_threads * runs_per_thread


def test_admin_service_training_and_evaluation_workflow(temp_admin_service):
    """Verify that training and evaluation hooks update metrics and activity correctly."""
    # 1. Training Started
    run_id = temp_admin_service.record_training_started(
        model_type="random_forest",
        dataset_id="ds-100",
        horizon=14,
    )
    assert run_id.startswith("run_")

    # 2. Training Completed
    temp_admin_service.record_training_completed(
        run_id=run_id,
        model_type="random_forest",
        metrics={"wape": 0.082, "mae": 15.2, "rmse": 22.1},
    )

    # 3. Model Evaluation Completed
    temp_admin_service.record_evaluation_completed(
        dataset_id="ds-100",
        horizon=14,
        primary_metric="wape",
        candidate_models=["Seasonal Naive", "Random Forest", "XGBoost"],
        comparison_table=[
            {"model_name": "Seasonal Naive", "metrics": {"wape": 0.12, "mae": 20.0, "rmse": 28.0}},
            {"model_name": "Random Forest", "metrics": {"wape": 0.082, "mae": 15.2, "rmse": 22.1}},
            {"model_name": "XGBoost", "metrics": {"wape": 0.075, "mae": 13.8, "rmse": 19.5}},
        ],
        winning_model="XGBoost",
    )

    dashboard = temp_admin_service.get_dashboard_summary()
    assert dashboard["total_training_runs"] == 1
    assert dashboard["total_evaluated_models"] == 3

    perf = temp_admin_service.get_performance_summary()
    assert perf["training_and_testing"]["has_evaluations"] is True
    assert perf["training_and_testing"]["best_performing_model"] == "XGBoost"

    # Model Comparison section
    assert perf["model_comparison"]["has_data"] is True
    assert len(perf["model_comparison"]["comparison_table"]) == 3


def test_admin_service_operational_forecast_verification(temp_admin_service):
    """Verify that operational metrics are calculated only when actual observations are provided."""
    # Initially no forecasts
    perf_init = temp_admin_service.get_performance_summary()
    assert perf_init["operational_forecasts"]["has_operational_evaluations"] is False
    assert perf_init["operational_forecasts"]["mae"] is None

    # Generate forecast
    event_id = temp_admin_service.record_forecast_generated(
        dataset_id="ds-100",
        model_name="XGBoost Regressor",
        horizon=3,
        points_count=3,
        forecast_points=[
            {"date": "2026-10-01", "predicted_demand": 100.0},
            {"date": "2026-10-02", "predicted_demand": 110.0},
            {"date": "2026-10-03", "predicted_demand": 120.0},
        ],
    )

    # Verify against actual observations
    actual_data = [
        {"date": "2026-10-01", "demand": 95.0},
        {"date": "2026-10-02", "demand": 115.0},
        {"date": "2026-10-03", "demand": 125.0},
    ]

    metrics = temp_admin_service.verify_forecast_operational(
        event_id=event_id,
        actual_observations=actual_data,
    )
    assert metrics is not None
    assert metrics["matched_periods"] == 3
    assert metrics["mae"] == 5.0
    assert metrics["wape"] > 0

    perf_after = temp_admin_service.get_performance_summary()
    assert perf_after["operational_forecasts"]["has_operational_evaluations"] is True
    assert perf_after["operational_forecasts"]["mae"] == 5.0


def test_admin_authentication_and_route_protection():
    """Verify that admin endpoints require authentication and reject unauthorized requests."""
    client = TestClient(app)

    # 1. Unauthenticated requests must return 401
    res = client.get("/api/v1/admin/dashboard")
    assert res.status_code == 401

    res = client.get("/api/v1/admin/performance")
    assert res.status_code == 401

    res = client.get("/api/v1/admin/system-info")
    assert res.status_code == 401

    # 2. Login with wrong password must return 401
    bad_login = client.post(
        "/api/v1/admin/login",
        json={"username": settings.ADMIN_USERNAME, "password": "wrong_password_123"},
    )
    assert bad_login.status_code == 401

    # 3. Login with correct credentials must succeed
    good_login = client.post(
        "/api/v1/admin/login",
        json={"username": settings.ADMIN_USERNAME, "password": settings.ADMIN_PASSWORD},
    )
    assert good_login.status_code == 200
    token_data = good_login.json()
    token = token_data["token"]
    assert token.startswith("adm_")

    headers = {"Authorization": f"Bearer {token}"}

    # 4. Access protected dashboard
    dash_res = client.get("/api/v1/admin/dashboard", headers=headers)
    assert dash_res.status_code == 200
    data = dash_res.json()
    assert "total_training_runs" in data
    assert "model_statuses" in data

    # 5. Access performance summary
    perf_res = client.get("/api/v1/admin/performance", headers=headers)
    assert perf_res.status_code == 200
    pdata = perf_res.json()
    assert "training_and_testing" in pdata
    assert "operational_forecasts" in pdata
    assert "model_comparison" in pdata

    # 6. Access system info
    info_res = client.get("/api/v1/admin/system-info", headers=headers)
    assert info_res.status_code == 200
    idata = info_res.json()
    assert "library_versions" in idata
    assert "fastapi" in idata["library_versions"]
    assert "xgboost" in idata["library_versions"]

    # 7. Logout revokes token
    logout_res = client.post("/api/v1/admin/logout", headers=headers)
    assert logout_res.status_code == 200

    # Token must now be rejected
    res_after_logout = client.get("/api/v1/admin/dashboard", headers=headers)
    assert res_after_logout.status_code == 401
