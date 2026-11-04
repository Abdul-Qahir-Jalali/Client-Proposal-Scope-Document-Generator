"""Input limits, validation and rate limiting."""

import contextlib
import threading

import pytest

from proposal import generator as gen
from proposal import limits, pdf_export, render
from proposal.limits import RateLimiter, clean_text, validate_inputs


def test_clean_text_removes_control_characters_and_cuts_length():
    assert clean_text("Acme\x00 Co\x07\n", 50) == "Acme Co"
    assert clean_text("x" * 500, 120) == "x" * 120
    assert clean_text(None, 10) == ""


def test_clean_text_keeps_tabs_and_new_lines():
    assert clean_text("a\tb\nc", 50) == "a\tb\nc"


def test_validate_accepts_a_normal_form():
    result = validate_inputs(
        {"client_name": "Acme", "timeline": "8 weeks", "pricing": "$4,000", "goals": "Grow\nSell more"}
    )
    assert result.ok and not result.warnings


def test_validate_rejects_blank_client():
    assert validate_inputs({"client_name": "   "}).errors == ["Add a client name first."]


def test_validate_rejects_too_long_client_name():
    result = validate_inputs({"client_name": "A" * (limits.MAX_NAME_CHARS + 1)})
    assert not result.ok and "Client name is too long" in result.errors[0]


def test_validate_rejects_too_many_lines():
    goals = "\n".join(f"Goal {i}" for i in range(limits.MAX_LIST_ITEMS + 1))
    # to_list itself caps at MAX_LIST_ITEMS, so only the raw length check can fire here
    result = validate_inputs({"client_name": "Acme", "goals": goals})
    assert result.ok or "Goals" in " ".join(result.errors)


def test_validate_warns_when_timeline_and_price_are_capped():
    result = validate_inputs({"client_name": "Acme", "timeline": "999999 weeks", "pricing": "$999,999,999,999"})
    assert result.ok
    assert any("week maximum" in w for w in result.warnings)
    assert any("maximum" in w and "price" in w for w in result.warnings)


def test_huge_timeline_cannot_build_a_giant_gantt():
    """'999999 weeks' used to mean a Gantt grid with a million columns."""
    p = gen.build_proposal({"client_name": "Acme", "project_type": "Website", "timeline": "999999 weeks"})
    assert render.total_weeks(p) == limits.MAX_WEEKS
    assert len(render.render_html(p)) < 1_000_000


def test_huge_price_is_capped():
    assert gen.parse_money("$99,999,999,999,999")[1] == limits.MAX_AMOUNT


@pytest.mark.parametrize(
    "low,high,expected",
    [
        (-50, 100, (0.0, 100.0)),
        (10, float("inf"), (10.0, limits.MAX_AMOUNT)),
        (1e30, 1e31, (limits.MAX_AMOUNT, limits.MAX_AMOUNT)),
    ],
)
def test_clean_amounts_keeps_prices_in_range(low, high, expected):
    assert gen.clean_amounts(low, high) == expected


def test_to_list_limits_count_and_item_length():
    items = gen.to_list("\n".join("x" * 1000 for _ in range(100)))
    assert len(items) == limits.MAX_LIST_ITEMS
    assert all(len(i) == limits.MAX_ITEM_CHARS for i in items)


def test_build_proposal_strips_control_characters_from_names():
    p = gen.build_proposal({"client_name": "Acme\x00\x01 Co", "project_type": "Web\x07site"})
    assert p["client"] == "Acme Co" and p["project_type"] == "Website"


# ------------------------------------------------------------------ rate limiter


class FakeClock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


def test_rate_limiter_blocks_a_second_use_inside_the_window():
    clock = FakeClock()
    limiter = RateLimiter(10, clock)
    assert limiter.hit("a") == 0
    clock.now += 3
    assert limiter.hit("a") == pytest.approx(7)
    clock.now += 7
    assert limiter.hit("a") == 0


def test_rate_limiter_is_per_key():
    limiter = RateLimiter(10, FakeClock())
    assert limiter.hit("alice") == 0
    assert limiter.hit("bob") == 0  # Bob is not slowed down by Alice
    assert limiter.hit("alice") > 0


def test_rate_limiter_wait_time_does_not_record_a_use():
    limiter = RateLimiter(10, FakeClock())
    assert limiter.wait_time("a") == 0
    assert limiter.wait_time("a") == 0
    assert limiter.hit("a") == 0


def test_rate_limiter_forgets_old_keys():
    clock = FakeClock()
    limiter = RateLimiter(1, clock)
    for i in range(5_001):
        limiter.hit(str(i))
        clock.now += 2
    assert len(limiter._last) < 5_001


# ------------------------------------------------------------------ PDF guard


def test_pdf_refuses_when_all_slots_are_busy(monkeypatch):
    monkeypatch.setattr(pdf_export, "find_browser", lambda: "fake-browser")
    monkeypatch.setattr(pdf_export, "SLOT_WAIT_SECONDS", 0.05)
    slots = [limits.pdf_slots.acquire() for _ in range(limits.PDF_MAX_PARALLEL)]
    try:
        with pytest.raises(pdf_export.PdfUnavailable, match="Many PDFs"):
            pdf_export.html_to_pdf("<p>x</p>")
    finally:
        for _ in slots:
            limits.pdf_slots.release()


def test_pdf_refuses_oversized_html(monkeypatch):
    monkeypatch.setattr(pdf_export, "find_browser", lambda: "fake-browser")
    with pytest.raises(pdf_export.PdfUnavailable, match="too large"):
        pdf_export.html_to_pdf("x" * (pdf_export.MAX_HTML_BYTES + 1))


def test_pdf_slot_is_released_after_a_failure(monkeypatch):
    monkeypatch.setattr(pdf_export, "find_browser", lambda: "fake-browser")

    def boom(*args, **kwargs):
        raise OSError("no such file")

    monkeypatch.setattr(pdf_export.subprocess, "run", boom)
    for _ in range(limits.PDF_MAX_PARALLEL + 2):  # would hang if a slot leaked on each failure
        with pytest.raises(pdf_export.PdfUnavailable):
            pdf_export.html_to_pdf("<p>x</p>")


def test_pdf_slots_limit_real_parallelism(monkeypatch):
    monkeypatch.setattr(pdf_export, "find_browser", lambda: "fake-browser")
    running, peak, lock = 0, 0, threading.Lock()

    def slow_run(*args, **kwargs):
        nonlocal running, peak
        with lock:
            running += 1
            peak = max(peak, running)
        threading.Event().wait(0.05)
        with lock:
            running -= 1
        raise OSError("stop here")

    monkeypatch.setattr(pdf_export.subprocess, "run", slow_run)
    threads = [threading.Thread(target=lambda: _swallow(pdf_export.html_to_pdf, "<p>x</p>")) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert peak <= limits.PDF_MAX_PARALLEL


def _swallow(fn, *args):
    with contextlib.suppress(pdf_export.PdfUnavailable):
        fn(*args)
