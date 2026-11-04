"""Shared test setup."""

import pytest

from proposal import limits


@pytest.fixture(autouse=True)
def _no_rate_limits_by_default(monkeypatch):
    """Most tests click buttons back to back, so switch the per-session waits off.

    Tests of the rate limits themselves set their own values (see tests/test_limits.py).
    """
    monkeypatch.setattr(limits.generate_limiter, "min_seconds", 0.0)
    monkeypatch.setattr(limits.pdf_limiter, "min_seconds", 0.0)
    monkeypatch.setenv("LOG_FILE", "none")  # tests must not write logs/app.log
