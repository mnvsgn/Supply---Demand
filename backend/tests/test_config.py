"""
Tests for configuration management, python-dotenv loading, and strict zero-fallback behavior.
"""

import os
from pydantic import ValidationError
import pytest
from app.core.config import Settings, settings


def test_settings_loaded_from_dotenv():
    """Verify that settings are loaded strictly from .env via python-dotenv."""
    assert settings.PROJECT_NAME == "Supply and Demand Forecasting"
    assert settings.PORT == 8000
    assert settings.HOST == "0.0.0.0"
    assert settings.LOG_LEVEL == "INFO"
    assert settings.ENVIRONMENT == "development"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.MAX_UPLOAD_SIZE_MB == 25
    assert settings.SESSION_EXPIRY_MINUTES == 60
    assert settings.SESSION_IDLE_TIMEOUT_MINUTES == 30
    assert settings.SESSION_CLEANUP_INTERVAL_MINUTES == 15
    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) == 2


def test_settings_strictly_rejects_missing_env_without_fallback(monkeypatch):
    """
    CRITICAL REQUIREMENT TEST:
    Verify that removing an environment variable causes Pydantic to raise an explicit
    ValidationError, proving that NO silent fallback defaults exist in Settings.
    """
    # Create isolated environment missing required fields
    isolated_env = {
        # Deliberately omit PROJECT_NAME and PORT
        "VERSION": "0.1.0",
        "API_V1_STR": "/api/v1",
        "ENVIRONMENT": "development",
        "DEBUG": "true",
        "HOST": "0.0.0.0",
        "CORS_ORIGINS": "http://localhost:5173",
        "LOG_LEVEL": "INFO",
        "SESSION_EXPIRY_MINUTES": "60",
        "SESSION_IDLE_TIMEOUT_MINUTES": "30",
        "SESSION_CLEANUP_INTERVAL_MINUTES": "15",
        "MAX_UPLOAD_SIZE_MB": "25",
        "STORAGE_DIR": "temp_storage/datasets",
        "SESSION_STORAGE_DIR": "temp_storage/sessions",
        "MAX_ROWS": "1000000",
        "MIN_ROWS": "1",
        "MAX_COLS": "200",
        "MIN_COLS": "2",
        "PREVIEW_ROWS": "5",
        "LLM_ENABLED": "false",
        "LLM_PROVIDER": "none",
        "LLM_API_KEY": "dummy",
        "LLM_MODEL": "gpt-4o-mini",
        "ADMIN_USERNAME": "admin",
        "ADMIN_PASSWORD": "demandiq_admin_2026",
    }

    # Clear current os.environ of PROJECT_NAME and PORT
    for key in list(os.environ.keys()):
        monkeypatch.delenv(key, raising=False)

    for k, v in isolated_env.items():
        monkeypatch.setenv(k, v)

    # Must fail because PROJECT_NAME and PORT have NO fallbacks!
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    error_fields = [err["loc"][0] for err in exc_info.value.errors()]
    assert "PROJECT_NAME" in error_fields
    assert "PORT" in error_fields


def test_settings_strictly_rejects_invalid_values_without_fallback(monkeypatch):
    """
    Verify that invalid values (e.g. invalid LOG_LEVEL or DEBUG) raise explicit
    ValidationErrors rather than falling back to default values.
    """
    valid_env = {
        "PROJECT_NAME": "Test App",
        "VERSION": "0.1.0",
        "API_V1_STR": "/api/v1",
        "ENVIRONMENT": "test",
        "DEBUG": "true",
        "HOST": "127.0.0.1",
        "PORT": "8000",
        "CORS_ORIGINS": "http://localhost:3000",
        "LOG_LEVEL": "INVALID_LEVEL",  # Invalid
        "SESSION_EXPIRY_MINUTES": "60",
        "SESSION_IDLE_TIMEOUT_MINUTES": "30",
        "SESSION_CLEANUP_INTERVAL_MINUTES": "15",
        "MAX_UPLOAD_SIZE_MB": "25",
        "STORAGE_DIR": "temp_storage/datasets",
        "SESSION_STORAGE_DIR": "temp_storage/sessions",
        "MAX_ROWS": "1000",
        "MIN_ROWS": "1",
        "MAX_COLS": "10",
        "MIN_COLS": "2",
        "PREVIEW_ROWS": "5",
        "LLM_ENABLED": "false",
        "LLM_PROVIDER": "none",
        "LLM_API_KEY": "none",
        "LLM_MODEL": "none",
        "ADMIN_USERNAME": "admin",
        "ADMIN_PASSWORD": "demandiq_admin_2026",
    }

    for key in list(os.environ.keys()):
        monkeypatch.delenv(key, raising=False)

    for k, v in valid_env.items():
        monkeypatch.setenv(k, v)

    # Invalid LOG_LEVEL must raise ValueError / ValidationError without falling back to INFO
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None)

    assert "LOG_LEVEL" in [e["loc"][0] for e in exc.value.errors()]

