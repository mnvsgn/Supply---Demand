from functools import lru_cache
from pathlib import Path
from typing import Any, List, Union
from dotenv import find_dotenv, load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Locate backend directory
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent

# Explicitly load .env using python-dotenv library
_env_path = BACKEND_ROOT / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path, override=False)
else:
    load_dotenv(find_dotenv(usecwd=True), override=False)


class Settings(BaseSettings):
    """
    Application Settings strictly loaded from environment variables and .env file.
    No fallback defaults are provided for environment configurations.
    Missing environment variables will raise an explicit validation error.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core Application Settings (No fallbacks)
    PROJECT_NAME: str
    VERSION: str
    API_V1_STR: str
    ENVIRONMENT: str
    DEBUG: bool

    # Networking & Server
    HOST: str
    PORT: int

    # CORS
    CORS_ORIGINS: Union[List[str], str]

    # Logging & Session Expiry
    LOG_LEVEL: str
    SESSION_EXPIRY_MINUTES: int
    SESSION_IDLE_TIMEOUT_MINUTES: int
    SESSION_CLEANUP_INTERVAL_MINUTES: int
    MAX_UPLOAD_SIZE_MB: Union[int, float]

    # Storage & Upload Limits
    STORAGE_DIR: str
    SESSION_STORAGE_DIR: str
    MAX_ROWS: int
    MIN_ROWS: int
    MAX_COLS: int
    MIN_COLS: int
    PREVIEW_ROWS: int

    # Optional LLM Integration Settings
    LLM_ENABLED: bool
    LLM_PROVIDER: str
    LLM_API_KEY: str
    LLM_MODEL: str

    # Admin Authentication Credentials (Strictly loaded from .env without fallbacks)
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str

    @property
    def max_upload_size_bytes(self) -> int:
        return int(float(self.MAX_UPLOAD_SIZE_MB) * 1024 * 1024)

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            val = v.strip().lower()
            if val in ("true", "1", "yes", "development", "dev", "debug"):
                return True
            if val in ("false", "0", "no", "release", "prod", "production"):
                return False
        raise ValueError(f"Invalid boolean value for DEBUG: {v}")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            parsed_list = [i.strip() for i in v.split(",") if i.strip()]
            if parsed_list:
                return parsed_list
        elif isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]

        raise ValueError(f"Invalid CORS_ORIGINS format: {v}")

    @field_validator("STORAGE_DIR", "SESSION_STORAGE_DIR", mode="after")
    @classmethod
    def resolve_storage_paths(cls, v: str) -> str:
        p = Path(v)
        if not p.is_absolute():
            return str((BACKEND_ROOT / p).resolve())
        return str(p.resolve())

    @field_validator("LOG_LEVEL", mode="after")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        val = v.strip().upper()
        if val not in levels:
            raise ValueError(f"Invalid LOG_LEVEL '{v}'. Must be one of {levels}")
        return val


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
