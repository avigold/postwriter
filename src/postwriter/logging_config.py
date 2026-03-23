"""Structured logging configuration for postwriter.

Logs to both console (concise) and a file (detailed with full context).
The file log is JSON-lines format for easy parsing and diagnosis.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON lines for the file handler."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1]:
            entry["exception"] = self.formatException(record.exc_info)
        # Capture any extra fields attached to the record
        for key in ("agent_role", "model_tier", "scene_id", "chapter_id",
                     "manuscript_id", "validator", "tokens_in", "tokens_out",
                     "branch_label", "score", "duration_ms", "phase"):
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        return json.dumps(entry, default=str)


class ConsoleFormatter(logging.Formatter):
    """Concise colored formatter for console output."""

    COLORS = {
        "DEBUG": "\033[90m",     # grey
        "INFO": "\033[36m",      # cyan
        "WARNING": "\033[33m",   # yellow
        "ERROR": "\033[31m",     # red
        "CRITICAL": "\033[1;31m",# bold red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        level = record.levelname[0]  # Single letter: I, W, E, D
        name = record.name.replace("postwriter.", "")
        msg = record.getMessage()

        # Add context if available
        extras = []
        for key in ("agent_role", "scene_id", "branch_label", "validator"):
            val = getattr(record, key, None)
            if val is not None:
                extras.append(f"{key}={val}")
        suffix = f" [{', '.join(extras)}]" if extras else ""

        return f"{color}{level} {name}: {msg}{suffix}{self.RESET}"


def setup_logging(
    log_dir: Path | None = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
) -> Path:
    """Configure logging for a postwriter session.

    Returns the path to the log file.
    """
    log_dir = log_dir or Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"postwriter_{timestamp}.jsonl"

    root = logging.getLogger("postwriter")
    root.setLevel(logging.DEBUG)

    # Clear any existing handlers
    root.handlers.clear()

    # Console handler — concise, INFO+ by default
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(console_level)
    console.setFormatter(ConsoleFormatter())
    root.addHandler(console)

    # File handler — detailed JSON lines, DEBUG+
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(file_level)
    file_handler.setFormatter(JSONFormatter())
    root.addHandler(file_handler)

    # Quiet down noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    root.info("Logging initialised", extra={"phase": "startup", "log_file": str(log_file)})

    return log_file
