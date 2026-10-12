import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    """Configures application-wide logging."""
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s"
    log_level = getattr(logging, settings.LOG_LEVEL.upper())

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )

    # Suppress overly verbose third-party loggers if not in DEBUG mode
    if not settings.DEBUG:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


logger = logging.getLogger("supply_demand_app")
