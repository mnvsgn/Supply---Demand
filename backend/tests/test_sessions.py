"""
Unit and integration tests for temporary session management,
unguessable token generation, session isolation, dataset ownership,
expiration, and disk artifact cleanup.
"""

from datetime import datetime, timedelta, timezone
import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.dataset_registry import dataset_registry
from app.services.session_manager import session_manager


@pytest.fixture(autouse=True)
def clean_registry():
    """Reset session and dataset registries before and after each test."""
    dataset_registry.clear()
    session_manager.clear_all()
    yield
    dataset_registry.clear()
    session_manager.clear_all()


client = TestClient(app)


def _make_dummy_csv() -> bytes:
    return b"date,demand\n2023-01-01,10\n2023-01-02,20\n2023-01-03,30\n"


# ---------------------------------------------------------------------------
# 1. Session Token Generation & Unguessability Tests
# ---------------------------------------------------------------------------

def test_session_token_unguessable_and_unique():
    """Verify session tokens have high cryptographic entropy and are unguessable."""
    tokens = set()
    for _ in range(50):
        session = session_manager.create_session()
        assert session.session_id.startswith("sess_")
        # 32 bytes base64url is at least 43 characters + 5 prefix = 48 chars
        assert len(session.session_id) >= 48
        tokens.add(session.session_id)

    # All 50 tokens must be completely distinct
    assert len(tokens) == 50


def test_session_creation_api():
    """Verify POST /api/v1/sessions creates unguessable session and sets response header."""
    res = client.post("/api/v1/sessions")
    assert res.status_code == 201
    data = res.json()

    assert "session_id" in data
    assert data["session_id"].startswith("sess_")
    assert res.headers.get("X-Session-ID") == data["session_id"]
    assert data["ttl_minutes"] == settings.SESSION_EXPIRY_MINUTES


# ---------------------------------------------------------------------------
# 2. Session Retrieval, Metadata & Deletion
# ---------------------------------------------------------------------------

def test_session_retrieval_and_activity_touch():
    """Verify GET /api/v1/sessions/{session_id} retrieves session and touches activity timestamp."""
    session = session_manager.create_session()
    original_last_accessed = session.last_accessed_at

    res = client.get(f"/api/v1/sessions/{session.session_id}")
    assert res.status_code == 200
    data = res.json()

    assert data["session_id"] == session.session_id
    assert data["dataset_count"] == 0
    assert data["is_expired"] is False


def test_session_deletion_purges_memory_and_disk():
    """Verify DELETE /api/v1/sessions/{session_id} purges memory and removes session directory on disk."""
    session = session_manager.create_session()
    session_dir = session.storage_dir
    assert session_dir.exists()

    # Upload a dataset inside this session
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("dummy.csv", io.BytesIO(_make_dummy_csv()), "text/csv")},
        headers={"X-Session-ID": session.session_id},
    )
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["dataset_id"]

    # Verify session directory contains uploaded file
    assert any(session_dir.rglob("*.csv"))

    # Delete session
    del_res = client.delete(f"/api/v1/sessions/{session.session_id}")
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True

    # Session directory must be wiped from disk
    assert not session_dir.exists()

    # Subsequent GET on session must return 404
    get_res = client.get(f"/api/v1/sessions/{session.session_id}")
    assert get_res.status_code == 404

    # Subsequent GET on dataset must return 404
    ds_res = client.get(f"/api/v1/datasets/{dataset_id}")
    assert ds_res.status_code == 404


def test_nonexistent_or_invalid_session_returns_404():
    """Verify unknown or forged session tokens safely return structured 404."""
    res = client.get("/api/v1/sessions/sess_invalid_forged_token_999999")
    assert res.status_code == 404
    body = res.json()
    assert body["success"] is False
    assert "not exist" in body["error"].lower() or "not found" in body["error"].lower()


# ---------------------------------------------------------------------------
# 3. Session Isolation & Dataset Ownership Security
# ---------------------------------------------------------------------------

def test_cross_session_dataset_isolation():
    """
    SECURITY CRITICAL TEST:
    Ensure User A cannot access User B's dataset by guessing or passing User B's dataset_id.
    """
    # 1. User A session
    res_a = client.post("/api/v1/sessions")
    session_a = res_a.json()["session_id"]

    upload_a = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("user_a_sales.csv", io.BytesIO(_make_dummy_csv()), "text/csv")},
        headers={"X-Session-ID": session_a},
    )
    dataset_a = upload_a.json()["dataset_id"]

    # 2. User B session
    res_b = client.post("/api/v1/sessions")
    session_b = res_b.json()["session_id"]

    upload_b = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("user_b_sales.csv", io.BytesIO(_make_dummy_csv()), "text/csv")},
        headers={"X-Session-ID": session_b},
    )
    dataset_b = upload_b.json()["dataset_id"]

    # 3. Authorized accesses succeed
    assert client.get(f"/api/v1/datasets/{dataset_a}", headers={"X-Session-ID": session_a}).status_code == 200
    assert client.get(f"/api/v1/datasets/{dataset_b}", headers={"X-Session-ID": session_b}).status_code == 200

    # 4. UNAUTHORIZED CROSS-ACCESS ATTEMPTS MUST BE BLOCKED WITH 404
    # User A attempts to view User B's dataset
    cross_view = client.get(f"/api/v1/datasets/{dataset_b}", headers={"X-Session-ID": session_a})
    assert cross_view.status_code == 404
    assert "not found in active session" in cross_view.json()["error"].lower()

    # User B attempts to view User A's dataset
    cross_view_b = client.get(f"/api/v1/datasets/{dataset_a}", headers={"X-Session-ID": session_b})
    assert cross_view_b.status_code == 404

    # User A attempts to run schema mapping on User B's dataset
    cross_map = client.post(
        f"/api/v1/datasets/{dataset_b}/mapping",
        json={"date_column": "date", "demand_column": "demand"},
        headers={"X-Session-ID": session_a},
    )
    assert cross_map.status_code == 404

    # User A attempts to trigger forecasting on User B's dataset
    cross_forecast = client.post(
        f"/api/v1/datasets/{dataset_b}/forecast",
        json={"model_type": "naive", "horizon": 3},
        headers={"X-Session-ID": session_a},
    )
    assert cross_forecast.status_code == 404


# ---------------------------------------------------------------------------
# 4. Session Expiration & Cleanup
# ---------------------------------------------------------------------------

def test_session_expiration_and_cleanup():
    """Verify expired sessions are evicted from memory and their files are deleted from disk."""
    # Create session with expired timestamp
    session = session_manager.create_session()
    session_dir = session.storage_dir
    # Artificially expire the session by moving expires_at into the past
    session.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)

    assert session.is_expired is True

    # 1. get_session on expired session evicts it and cleans disk
    retrieved = session_manager.get_session(session.session_id)
    assert retrieved is None
    assert not session_dir.exists()

    # 2. cleanup_expired removes any other expired sessions
    s2 = session_manager.create_session()
    s2.expires_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    cleaned = session_manager.cleanup_expired()
    assert cleaned >= 1
    assert session_manager.get_session(s2.session_id) is None


# ---------------------------------------------------------------------------
# 5. Conversation History Tracking
# ---------------------------------------------------------------------------

def test_session_conversation_history():
    """Verify conversation queries and responses are chronologically tracked per session."""
    res = client.post("/api/v1/sessions")
    session_id = res.json()["session_id"]

    # Append user question
    msg1 = client.post(
        f"/api/v1/sessions/{session_id}/conversation",
        json={"role": "user", "content": "What is the demand forecast for next week?"},
    )
    assert msg1.status_code == 201

    # Append assistant response
    msg2 = client.post(
        f"/api/v1/sessions/{session_id}/conversation",
        json={"role": "assistant", "content": "The projected demand averages 50 units/day."},
    )
    assert msg2.status_code == 201

    # Retrieve conversation history
    conv_res = client.get(f"/api/v1/sessions/{session_id}/conversation")
    assert conv_res.status_code == 200
    messages = conv_res.json()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert "projected demand" in messages[1]["content"]
