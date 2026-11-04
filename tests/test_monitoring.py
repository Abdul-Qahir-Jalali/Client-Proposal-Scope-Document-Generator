"""Logging, error tracking and the health check."""

import json
import logging
import sys

import pytest

from proposal import health, monitoring
from proposal.monitoring import JsonFormatter, get_logger, log_event, report_error, timed


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


@pytest.fixture
def records():
    """Collect everything the app logs during a test."""
    logger = get_logger()
    handler = ListHandler()
    old_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    yield handler.records
    logger.removeHandler(handler)
    logger.setLevel(old_level)


def _message(record):
    return record.getMessage(), getattr(record, "fields", {})


def test_timed_logs_duration_and_extra_fields(records):
    with timed("demo", kind="web") as info:
        info["count"] = 3
    message, fields = _message(records[-1])
    assert message == "demo done" and fields["kind"] == "web" and fields["count"] == 3
    assert isinstance(fields["ms"], int)


def test_timed_logs_failure_and_reraises(records):
    with pytest.raises(ValueError), timed("demo"):
        raise ValueError("boom")
    message, fields = _message(records[-1])
    assert message == "demo failed" and "ms" in fields
    assert records[-1].levelno == logging.WARNING


def test_report_error_returns_an_id_and_logs_the_traceback(records):
    try:
        raise RuntimeError("secret detail")
    except RuntimeError as exc:
        error_id = report_error(exc, "generate")
    assert len(error_id) == 8
    record = records[-1]
    assert record.levelno == logging.ERROR
    assert record.fields["error_id"] == error_id and record.fields["where"] == "generate"
    assert record.exc_info and record.exc_info[0] is RuntimeError


def test_json_formatter_makes_one_valid_json_line(records):
    log_event("proposal_generated", weeks=8)
    line = JsonFormatter().format(records[-1])
    data = json.loads(line)
    assert data["message"] == "proposal_generated" and data["weeks"] == 8 and data["level"] == "INFO"
    assert "\n" not in line


def test_json_formatter_includes_exception_text(records):
    try:
        raise KeyError("x")
    except KeyError as exc:
        report_error(exc, "test")
    assert "KeyError" in json.loads(JsonFormatter().format(records[-1]))["exception"]


def test_configure_logging_is_safe_to_call_many_times(monkeypatch):
    logger = get_logger()
    monkeypatch.setattr(logger, "_configured", False, raising=False)
    saved = logger.handlers[:]
    logger.handlers.clear()
    try:
        monkeypatch.setenv("LOG_FILE", "none")
        monitoring.configure_logging()
        monitoring.configure_logging()
        monitoring.configure_logging()
        assert len(logger.handlers) == 1  # Streamlit reruns the script on every click
    finally:
        logger.handlers[:] = saved


def test_log_file_is_created_and_rotates(tmp_path, monkeypatch):
    logger = get_logger()
    saved = logger.handlers[:]
    logger.handlers.clear()
    monkeypatch.setattr(logger, "_configured", False, raising=False)
    target = tmp_path / "logs" / "app.log"
    monkeypatch.setenv("LOG_FILE", str(target))
    monkeypatch.setenv("LOG_FORMAT", "json")
    try:
        monitoring.configure_logging()
        log_event("hello", n=1)
        for h in logger.handlers:
            h.flush()
        line = target.read_text(encoding="utf-8").splitlines()[-1]
        assert json.loads(line)["message"] == "hello"
        rotating = [h for h in logger.handlers if h.__class__.__name__ == "RotatingFileHandler"][0]
        assert rotating.maxBytes == 1_000_000 and rotating.backupCount == 5
    finally:
        for h in logger.handlers:
            h.close()
        logger.handlers[:] = saved


def test_error_tracking_is_off_without_a_dsn(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    assert monitoring.init_error_tracking() is False


def test_error_tracking_is_skipped_when_sentry_is_not_installed(monkeypatch, records):
    monkeypatch.setenv("SENTRY_DSN", "https://key@example.invalid/1")
    monkeypatch.setitem(sys.modules, "sentry_sdk", None)  # makes "import sentry_sdk" fail
    assert monitoring.init_error_tracking() is False
    assert any("not installed" in r.getMessage() for r in records)


def test_error_tracking_turns_on_with_a_dsn(monkeypatch):
    sentry_sdk = pytest.importorskip("sentry_sdk")
    seen = {}
    monkeypatch.setenv("SENTRY_DSN", "https://key@example.invalid/1")
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setattr(sentry_sdk, "init", lambda **kw: seen.update(kw))
    assert monitoring.init_error_tracking() is True
    assert seen["environment"] == "staging"
    assert seen["send_default_pii"] is False and seen["include_local_variables"] is False


# ------------------------------------------------------------------ app-level logging


def _app():
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    return AppTest.from_file(str(Path(__file__).resolve().parent.parent / "app.py"), default_timeout=60).run()


def _click(at, label):
    [b for b in at.button if b.label == label][0].click().run()


def test_generating_logs_an_event_without_client_data(records):
    at = _app()
    at.text_input(key="in_client").set_value("Very Secret Client Ltd").run()
    at.text_input(key="in_pricing").set_value("$12,345").run()
    _click(at, "Generate proposal")
    assert at.session_state.has_proposal
    generate = [r for r in records if r.getMessage() == "generate done"]
    assert generate and generate[-1].fields["mode"] == "Form" and "weeks" in generate[-1].fields
    everything = " ".join(r.getMessage() + str(getattr(r, "fields", "")) for r in records)
    assert "Very Secret" not in everything and "12,345" not in everything  # privacy rule


def test_unexpected_error_in_generate_shows_an_error_id_not_a_traceback(records, monkeypatch):
    from proposal import generator

    def boom(*a, **k):
        raise RuntimeError("internal detail that users must not see")

    monkeypatch.setattr(generator, "build_proposal", boom)
    at = _app()
    at.text_input(key="in_client").set_value("Acme").run()
    _click(at, "Generate proposal")
    assert not at.exception and not at.session_state.has_proposal
    shown = " ".join(w.value for w in at.sidebar.warning)
    assert "error id" in shown and "internal detail" not in shown
    error = [r for r in records if r.levelno == logging.ERROR][-1]
    assert error.fields["error_id"] in shown  # the id on screen matches the id in the log


# ------------------------------------------------------------------ health check


def test_health_check_passes_on_a_normal_install():
    results = health.run_checks()
    for name in ("samples", "generate_and_render", "word_export"):
        assert results[name]["ok"], results[name]
    assert results["pdf_browser"]["required"] is False


def test_health_main_exit_code_is_0_when_healthy_and_1_when_broken(monkeypatch, capsys):
    assert health.main() == 0
    capsys.readouterr()
    monkeypatch.setattr(health.generator, "load_samples", lambda *a, **k: {})
    assert health.main() == 1
    assert json.loads(capsys.readouterr().out)["healthy"] is False
