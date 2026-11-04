"""Input limits, validation and rate limiting.

Every number a user can type ends up in the proposal, the HTML preview, the Word file and the
PDF. Without limits, one huge value can freeze the app for everybody (for example a timeline of
"999999 weeks" would draw a million-column Gantt chart). All the limits live here so they are easy
to find and change.
"""

from __future__ import annotations

import re
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field

# --- Text size limits (characters) ---------------------------------------------------------
MAX_NAME_CHARS = 120  # client name, project type, prepared by
MAX_SHORT_CHARS = 200  # timeline, pricing
MAX_TEXT_CHARS = 6_000  # one multi-line box (goals, deliverables, notes, summary)
MAX_FREEFORM_CHARS = 20_000  # the whole pasted free-form text
MAX_ITEM_CHARS = 400  # one line item, milestone description or price item name
MAX_EDIT_CHARS = 16_000  # one box in the Edit tab (40 lines x 400 characters)

# --- Count limits ----------------------------------------------------------------------------
MAX_LIST_ITEMS = 40  # lines in one list (goals, deliverables, ...)
MAX_MILESTONES = 30
MAX_PRICE_ITEMS = 40

# --- Number limits -----------------------------------------------------------------------------
MAX_WEEKS = 104  # two years
MAX_AMOUNT = 1_000_000_000.0  # one billion

# --- Rate limits (see RateLimiter) ---------------------------------------------------------------
GENERATE_MIN_SECONDS = 1.0  # between two "Generate proposal" clicks in one session
PDF_MIN_SECONDS = 10.0  # between two PDF runs in one session
PDF_MAX_PARALLEL = 2  # PDF runs at the same time on the whole server

# Control characters (except tab, new line and carriage return) can break Word files and the PDF.
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(value: object, max_chars: int) -> str:
    """Make one piece of user text safe: remove control characters, trim, cut to `max_chars`."""
    text = _CONTROL_RE.sub("", str(value if value is not None else ""))
    return text.strip()[:max_chars]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass
class ValidationResult:
    """Problems that stop a proposal from being generated, and notes about things we trimmed."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


# Input field -> (label shown to the user, character limit)
_FIELD_LIMITS: dict[str, tuple[str, int]] = {
    "client_name": ("Client name", MAX_NAME_CHARS),
    "project_type": ("Project type", MAX_NAME_CHARS),
    "prepared_by": ("Prepared by", MAX_NAME_CHARS),
    "timeline": ("Timeline", MAX_SHORT_CHARS),
    "pricing": ("Pricing", MAX_SHORT_CHARS),
    "goals": ("Goals", MAX_TEXT_CHARS),
    "deliverables": ("Deliverables", MAX_TEXT_CHARS),
    "notes": ("Notes", MAX_TEXT_CHARS),
}


def validate_inputs(inputs: dict) -> ValidationResult:
    """Check the raw form values before they are turned into a proposal."""
    from .generator import parse_money, parse_weeks, to_list  # local import: generator imports this module

    result = ValidationResult()
    if not str(inputs.get("client_name") or "").strip():
        result.errors.append("Add a client name first.")
    for key, (label, limit) in _FIELD_LIMITS.items():
        length = len(str(inputs.get(key) or ""))
        if length > limit:
            result.errors.append(f"{label} is too long ({length:,} characters). The limit is {limit:,}.")
    for key in ("goals", "deliverables", "notes"):
        count = len(to_list(inputs.get(key), split_commas=(key == "deliverables")))
        if count > MAX_LIST_ITEMS:
            result.errors.append(f"{_FIELD_LIMITS[key][0]} has {count} lines. The limit is {MAX_LIST_ITEMS}.")
        too_long = [i for i in to_list(inputs.get(key)) if len(i) > MAX_ITEM_CHARS]
        if too_long:
            result.warnings.append(
                f"{_FIELD_LIMITS[key][0]}: {len(too_long)} long line(s) were shortened to {MAX_ITEM_CHARS} characters."
            )
    timeline = str(inputs.get("timeline") or "")
    if parse_weeks(timeline, cap=False) > MAX_WEEKS:
        result.warnings.append(f"The timeline was shortened to the {MAX_WEEKS}-week maximum.")
    if parse_money(str(inputs.get("pricing") or ""), cap=False)[1] > MAX_AMOUNT:
        result.warnings.append(f"The price was lowered to the {MAX_AMOUNT:,.0f} maximum.")
    return result


class RateLimiter:
    """Allow an action at most once per `min_seconds` for each key (for example a session id).

    `clock` can be replaced in tests so they do not have to wait.
    """

    def __init__(self, min_seconds: float, clock: Callable[[], float] = time.monotonic) -> None:
        self.min_seconds = min_seconds
        self._clock = clock
        self._last: dict[str, float] = {}
        self._lock = threading.Lock()

    def wait_time(self, key: str) -> float:
        """Seconds the caller must still wait. 0 means allowed now. Does not record a use."""
        with self._lock:
            last = self._last.get(key)
            if last is None:
                return 0.0
            return max(0.0, self.min_seconds - (self._clock() - last))

    def hit(self, key: str) -> float:
        """Try to use the action. Returns 0 when allowed (and records it), else the seconds to wait."""
        with self._lock:
            now = self._clock()
            last = self._last.get(key)
            if last is not None and now - last < self.min_seconds:
                return self.min_seconds - (now - last)
            self._last[key] = now
            # Forget old keys so the table cannot grow forever on a long-running server.
            if len(self._last) > 5_000:
                cutoff = now - self.min_seconds
                self._last = {k: t for k, t in self._last.items() if t > cutoff}
            return 0.0


# One shared gate for every PDF run on this server. A PDF run starts a whole browser process.
pdf_slots = threading.BoundedSemaphore(PDF_MAX_PARALLEL)


# One limiter per action, shared by every session in this server process. The key is a random
# per-session id, so one visitor clicking fast does not slow down anyone else.
generate_limiter = RateLimiter(GENERATE_MIN_SECONDS)
pdf_limiter = RateLimiter(PDF_MIN_SECONDS)
