"""
Integration tests for FastAPI foundation endpoints (health check, root info, error handling).
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    """Verify that the health endpoint at /api/v1/health returns 200 OK and valid payload."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data


def test_root_endpoint():
    """Verify that the root endpoint returns service information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "health" in data
    assert data["health"] == "/api/v1/health"


def test_404_error_structure():
    """Verify that unknown routes return consistent ErrorResponse structure."""
    response = client.get("/api/v1/non_existent_route")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert "code" in data
    assert data["code"] == "HTTP_404"
