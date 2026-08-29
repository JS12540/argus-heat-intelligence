"""Centralized logger setup. Configures console + file handlers once at import time."""

import logging
import logging.config

from argus_agent.src.config import REPO_ROOT
from argus_agent.src.constants import LOG_LEVEL

LOGS_DIR = REPO_ROOT / "logs"


def _configure() -> None:
    # Serverless platforms (Vercel, Lambda) ship a read-only filesystem outside /tmp — file
    # logging there just crashes at import time. They already capture stdout/stderr as logs,
    # so fall back to console-only instead of failing the whole app.
    file_logging_available = True
    try:
        (LOGS_DIR / "app").mkdir(parents=True, exist_ok=True)
        (LOGS_DIR / "audit").mkdir(parents=True, exist_ok=True)
    except OSError:
        file_logging_available = False

    app_handlers = ["console", "app_file"] if file_logging_available else ["console"]
    audit_handlers = ["console", "audit_file"] if file_logging_available else ["console"]

    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": LOG_LEVEL,
        },
    }
    if file_logging_available:
        handlers["app_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": str(LOGS_DIR / "app" / "app.log"),
            "maxBytes": 5_000_000,
            "backupCount": 3,
        }
        handlers["audit_file"] = {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": str(LOGS_DIR / "audit" / "audit.log"),
        }

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                },
            },
            "handlers": handlers,
            "loggers": {
                "argus.app": {
                    "handlers": app_handlers,
                    "level": LOG_LEVEL,
                    "propagate": False,
                },
                "argus.audit": {
                    "handlers": audit_handlers,
                    "level": "INFO",
                    "propagate": False,
                },
                # Silenced — these drown out our own labeled request/response lines with
                # one entry per poll (httpx) or per frontend refresh (uvicorn.access).
                "httpx": {"handlers": ["console"], "level": "WARNING", "propagate": False},
                "uvicorn.access": {"handlers": ["console"], "level": "WARNING", "propagate": False},
            },
            "root": {"handlers": ["console"], "level": LOG_LEVEL},
        }
    )


_configure()


def get_app_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"argus.app.{name}")


def get_audit_logger() -> logging.Logger:
    return logging.getLogger("argus.audit")
