"""Logging, error tracking and timing.

Settings come from environment variables, so nothing is hard-coded:

    LOG_LEVEL    DEBUG, INFO (default), WARNING, ERROR
    LOG_FORMAT   "text" (default, easy to read) or "json" (one JSON object per line, for log tools)
    LOG_FILE     path of a rotating log file. Default: logs/app.log. Set to "none" to log to the
                 console only.
    SENTRY_DSN   if set (and sentry-sdk is installed), crashes are sent to Sentry. Off by default.
    APP_ENV      name shown in Sentry, for example "production" or "staging". Default "development".

Privacy rule: never log client names, prices or any proposal text. Log counts, sizes and timings.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import sys
import time
import uuid
from collections.abc import Iterator
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGGER_NAME = "proposal"
DEFAULT_LOG_FILE = Path(__file__).resolve().parent.parent / "logs" / "app.log"

# Extra fields attached to a log record with `log.info("msg", extra={"fields": {...}})`
_FIELDS_ATTR = "fields"


class JsonFormatter(logging.Formatter):
    """One JSON object per line: easy to search and to load into a log tool."""

    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, object] = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        data.update(getattr(record, _FIELDS_ATTR, {}) or {})
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data, default=str)


class TextFormatter(logging.Formatter):
    """Readable line, with the extra fields as key=value pairs at the end."""

    def format(self, record: logging.LogRecord) -> str:
        line = super().format(record)
        fields = getattr(record, _FIELDS_ATTR, None)
        if fields:
            line += "  " + " ".join(f"{k}={v}" for k, v in fields.items())
        return line


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(f"{LOGGER_NAME}.{name}" if name else LOGGER_NAME)


def configure_logging() -> logging.Logger:
    """Set up logging once. Safe to call on every Streamlit rerun: it never adds handlers twice."""
    root = logging.getLogger(LOGGER_NAME)
    if getattr(root, "_configured", False):
        return root
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    root.setLevel(getattr(logging, level, logging.INFO))
    root.propagate = False
    formatter: logging.Formatter
    if os.environ.get("LOG_FORMAT", "text").lower() == "json":
        formatter = JsonFormatter()
    else:
        formatter = TextFormatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")

    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(formatter)
    root.addHandler(console)

    target = os.environ.get("LOG_FILE", str(DEFAULT_LOG_FILE))
    if target.lower() != "none":
        try:
            path = Path(target)
            path.parent.mkdir(parents=True, exist_ok=True)
            # 1 MB per file, keep 5 old files: the log can never fill the disk.
            handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
            handler.setFormatter(formatter)
            root.addHandler(handler)
        except OSError as exc:  # a read-only disk must not stop the app from starting
            root.warning("Log file %s could not be opened (%s). Logging to console only.", target, exc)
    root._configured = True  # type: ignore[attr-defined]
    init_error_tracking()
    return root


def init_error_tracking() -> bool:
    """Start Sentry when SENTRY_DSN is set. Returns True when it is active."""
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        return False
    try:
        import sentry_sdk
    except ImportError:
        get_logger().warning("SENTRY_DSN is set but sentry-sdk is not installed. Error tracking is off.")
        return False
    sentry_sdk.init(
        dsn=dsn,
        environment=os.environ.get("APP_ENV", "development"),
        send_default_pii=False,  # no IP addresses or cookies
        include_local_variables=False,  # local variables could hold proposal text
        traces_sample_rate=0.0,
    )
    get_logger().info("Error tracking is on.", extra={_FIELDS_ATTR: {"env": os.environ.get("APP_ENV", "development")}})
    return True


def report_error(exc: BaseException, where: str) -> str:
    """Log an unexpected error, send it to Sentry if on, and return a short id to show the user.

    The user sees only the id. Support can search the log (or Sentry) for it.
    """
    error_id = uuid.uuid4().hex[:8]
    get_logger().error(
        "Unexpected error in %s",
        where,
        exc_info=(type(exc), exc, exc.__traceback__),
        extra={_FIELDS_ATTR: {"error_id": error_id, "where": where}},
    )
    if os.environ.get("SENTRY_DSN", "").strip():
        try:
            import sentry_sdk

            with sentry_sdk.new_scope() as scope:
                scope.set_tag("error_id", error_id)
                scope.set_tag("where", where)
                sentry_sdk.capture_exception(exc)
        except ImportError:
            pass
    return error_id


@contextlib.contextmanager
def timed(event: str, **fields: object) -> Iterator[dict[str, object]]:
    """Log how long a block took, and whether it worked.

        with timed("pdf_export", sections=6) as info:
            ...
            info["bytes"] = len(pdf)

    Logs one line: `pdf_export done  ms=812 sections=6 bytes=48213`. A failure is logged as
    `pdf_export failed` and the exception continues upward unchanged.
    """
    extra: dict[str, object] = dict(fields)
    start = time.perf_counter()
    try:
        yield extra
    except BaseException:
        extra["ms"] = round((time.perf_counter() - start) * 1000)
        get_logger().warning("%s failed", event, extra={_FIELDS_ATTR: extra})
        raise
    extra["ms"] = round((time.perf_counter() - start) * 1000)
    get_logger().info("%s done", event, extra={_FIELDS_ATTR: extra})


def log_event(event: str, **fields: object) -> None:
    """One structured log line for something that happened, for example `proposal_generated`."""
    get_logger().info(event, extra={_FIELDS_ATTR: fields})
