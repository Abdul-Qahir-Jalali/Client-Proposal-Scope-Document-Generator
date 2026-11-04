"""Hero photo for the proposal cover, chosen from the project type.

One photo per project kind (web, app, marketing, brand, general) lives in `proposal/assets/hero/`. The chosen photo is
embedded in the HTML as a data URI, so the exported file is self-contained: it works offline, in email and in the PDF.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent / "assets" / "hero"
MAX_BYTES = 600_000  # a photo bigger than this would make every export heavy; it is ignored instead


@lru_cache(maxsize=16)
def hero_data_uri(kind: str) -> str | None:
    """The photo for `kind` as a data URI, or None (the cover then falls back to plain brand colour)."""
    for name in (kind, "general"):
        path = ASSETS_DIR / f"{name}.jpg"
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if 0 < len(data) <= MAX_BYTES:
            return "data:image/jpeg;base64," + base64.b64encode(data).decode("ascii")
    return None
