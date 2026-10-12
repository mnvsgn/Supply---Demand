"""
Convenience entry point for running the application directly from the `backend` root.
Usage:
    python main.py
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Load environment variables explicitly via python-dotenv
load_dotenv(dotenv_path=BACKEND_ROOT / ".env")

from app.main import app

if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        app_dir=str(BACKEND_ROOT),
    )
